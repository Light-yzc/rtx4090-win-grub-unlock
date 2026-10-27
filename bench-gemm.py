"""Benchmark RTX 4090 Tensor Core Unlock status (PTX mma.sync + PyTorch cuBLAS GEMM).

1. Raw Tensor Core instruction throughput (PTX mma.sync, 8 independent accumulator chains/warp):
   Directly measures the hardware instruction issue rate controlled by the AD102
   speed-select registers (SS0=0x88888888 / SS1=0x8):
     - FP16 -> FP16 accumulate : ~300-330 TFLOPS (always full rate)
     - FP16 -> FP32 accumulate : ~165 TFLOPS when LOCKED, ~300-330 TFLOPS when UNLOCKED!
     - BF16 -> FP32 accumulate : ~165 TFLOPS when LOCKED, ~300-330 TFLOPS when UNLOCKED!
     - TF32 -> FP32 accumulate :  ~82 TFLOPS when LOCKED, ~150-165 TFLOPS when UNLOCKED!

2. End-to-End PyTorch cuBLAS GEMM throughput across representative matrix shapes:
   Note: Standard 8192x8192x8192 GEMM is memory/L2/power-bound (~150-180 TFLOPS), whereas
   L2-resident tiles (e.g. 4096x4096x4096, 6144x6144x6144) and TF32 GEMM show significant
   end-to-end speedups once unlocked.
"""
import argparse
import ctypes
import torch


def bench_ptx_mma(cu: ctypes.WinDLL, sink: torch.Tensor, name: str, mma_inst: str, acc_regs: int, flops_per_inst: float, iters: int = 20000) -> dict:
    ptx = """
.version 8.0
.target sm_89
.address_size 64

.visible .entry k_bench(.param .u64 p_iters, .param .u64 p_out) {
    .reg .b64 %rd<4>;
    .reg .b32 %r<44>;
    .reg .pred %p<2>;
    ld.param.u64 %rd1, [p_iters];
    ld.param.u64 %rd2, [p_out];
    mov.u32 %r0, %tid.x;
    add.u32 %r1, %r0, 1;
"""
    for i in range(4, 36):
        ptx += f"    mov.b32 %r{i}, %r1;\n"
    ptx += """
    mov.u64 %rd3, 0;
LOOP:
"""
    for c in range(0, 32, 4):
        r0, r1, r2, r3 = 4 + c, 5 + c, 6 + c, 7 + c
        if acc_regs == 4:
            ptx += f"    {mma_inst} {{%r{r0}, %r{r1}, %r{r2}, %r{r3}}}, {{%r0, %r1, %r0, %r1}}, {{%r1, %r0}}, {{%r{r0}, %r{r1}, %r{r2}, %r{r3}}};\n"
        else:
            ptx += f"    {mma_inst} {{%r{r0}, %r{r1}}}, {{%r0, %r1, %r0, %r1}}, {{%r1, %r0}}, {{%r{r0}, %r{r1}}};\n"
    ptx += """
    add.u64 %rd3, %rd3, 1;
    setp.lt.u64 %p1, %rd3, %rd1;
    @%p1 bra LOOP;
    mov.u32 %r40, 0;
"""
    for i in range(4, 36):
        ptx += f"    xor.b32 %r40, %r40, %r{i};\n"
    ptx += """
    setp.eq.u32 %p1, %r40, 2147483647;
    @%p1 st.global.u32 [%rd2], %r40;
    ret;
}
"""
    mod = ctypes.c_void_p()
    res = cu.cuModuleLoadData(ctypes.byref(mod), ptx.encode("utf-8"))
    if res != 0:
        raise RuntimeError(f"cuModuleLoadData failed with CUDA error {res}")
    func = ctypes.c_void_p()
    cu.cuModuleGetFunction(ctypes.byref(func), mod, b"k_bench")

    c_iters = ctypes.c_uint64(iters)
    c_out = ctypes.c_uint64(sink.data_ptr())
    args = (ctypes.c_void_p * 2)(
        ctypes.cast(ctypes.byref(c_iters), ctypes.c_void_p),
        ctypes.cast(ctypes.byref(c_out), ctypes.c_void_p),
    )

    blocks, warps = 1056, 8
    # Warmup
    for _ in range(2):
        cu.cuLaunchKernel(func, blocks, 1, 1, warps * 32, 1, 1, 0, 0, args, 0)
    torch.cuda.synchronize()

    best_tflops = 0.0
    best_ms = 0.0
    for _ in range(3):
        s = torch.cuda.Event(enable_timing=True)
        e = torch.cuda.Event(enable_timing=True)
        s.record()
        cu.cuLaunchKernel(func, blocks, 1, 1, warps * 32, 1, 1, 0, 0, args, 0)
        e.record()
        torch.cuda.synchronize()
        ms = s.elapsed_time(e)
        total_flops = blocks * warps * iters * 8 * flops_per_inst
        tflops = total_flops / (ms * 1e-3) / 1e12
        if tflops > best_tflops:
            best_tflops = tflops
            best_ms = ms
    cu.cuModuleUnload(mod)
    return {"name": name, "ms": round(best_ms, 3), "tflops": round(best_tflops, 2)}


def bench_cublas_gemm(m: int, n: int, k: int, dtype: torch.dtype, label: str, warmup: int = 25, iters: int = 80) -> dict:
    torch.backends.cuda.matmul.allow_tf32 = True
    a = torch.randn((m, k), device="cuda", dtype=dtype)
    b = torch.randn((k, n), device="cuda", dtype=dtype)
    for _ in range(warmup):
        c = torch.matmul(a, b)
    torch.cuda.synchronize()

    s = torch.cuda.Event(enable_timing=True)
    e = torch.cuda.Event(enable_timing=True)
    s.record()
    for _ in range(iters):
        c = torch.matmul(a, b)
    e.record()
    torch.cuda.synchronize()
    ms = s.elapsed_time(e) / iters
    tflops = (2.0 * m * n * k) / (ms * 1e-3) / 1e12
    return {"label": label, "shape": f"{m}x{n}x{k}", "ms": round(ms, 3), "tflops": round(tflops, 2)}


def main() -> None:
    if not torch.cuda.is_available():
        raise SystemExit("CUDA is not available.")

    props = torch.cuda.get_device_properties(0)
    print(f"GPU: {props.name} ({props.total_memory // (1024*1024)} MiB, {props.multi_processor_count} SMs, CC {props.major}.{props.minor})")
    print(f"PyTorch: {torch.__version__} (CUDA {torch.version.cuda})")
    print("=" * 78)
    print("[1] Direct Tensor Core PTX mma.sync Instruction Throughput (Register-Resident)")
    print("-" * 78)

    sink = torch.zeros(1024, dtype=torch.int32, device="cuda")
    cu = ctypes.WinDLL("nvcuda.dll")

    ptx_modes = [
        ("FP16 -> FP16 (m16n8k16)", "mma.sync.aligned.m16n8k16.row.col.f16.f16.f16.f16", 2, 4096.0, "~330 TFLOPS"),
        ("FP16 -> FP32 (m16n8k16)", "mma.sync.aligned.m16n8k16.row.col.f32.f16.f16.f32", 4, 4096.0, "~165 Locked / ~330 Unlocked"),
        ("BF16 -> FP32 (m16n8k16)", "mma.sync.aligned.m16n8k16.row.col.f32.bf16.bf16.f32", 4, 4096.0, "~165 Locked / ~330 Unlocked"),
        ("TF32 -> FP32 (m16n8k8) ", "mma.sync.aligned.m16n8k8.row.col.f32.tf32.tf32.f32", 4, 2048.0, " ~82 Locked / ~165 Unlocked"),
    ]
    ptx_results = []
    for name, inst, regs, flops, ref in ptx_modes:
        r = bench_ptx_mma(cu, sink, name, inst, regs, flops)
        ptx_results.append(r)
        print(f"{r['name']:25s} | {r['ms']:7.3f} ms | {r['tflops']:7.2f} TFLOPS | Ref: {ref}")

    fp16_f16 = ptx_results[0]["tflops"]
    fp16_f32 = ptx_results[1]["tflops"]
    bf16_f32 = ptx_results[2]["tflops"]
    tf32_f32 = ptx_results[3]["tflops"]
    ratio = fp16_f32 / fp16_f16 if fp16_f16 > 0 else 0.0

    print("-" * 78)
    if fp16_f32 > 240.0 and ratio > 0.85:
        print(f"==> HARDWARE STATUS: UNLOCKED! (FP16->FP32 is {fp16_f32:.1f} TFLOPS, {ratio:.2f}x of FP16->FP16)")
    else:
        print(f"==> HARDWARE STATUS: LOCKED (FP16->FP32 is {fp16_f32:.1f} TFLOPS, {ratio:.2f}x of FP16->FP16)")

    print("=" * 78)
    print("[2] End-to-End PyTorch cuBLAS GEMM Throughput (Includes HBM/L2/Power Limits)")
    print("-" * 78)
    gemm_cases = [
        (2048, 2048, 2048, torch.bfloat16, "BF16 (FP32 acc, L2-resident) [Locked cap: 165.2]"),
        (4096, 4096, 4096, torch.float16,  "FP16 (FP32 acc, L2-resident) [Locked cap: 165.2]"),
        (6144, 6144, 6144, torch.float32,  "TF32 (FP32 acc)              [Locked cap:  82.6]"),
        (8192, 8192, 8192, torch.float16,  "FP16 (FP32 acc, 450W/VRAM bound)"),
    ]
    for m, n, k, dt, label in gemm_cases:
        g = bench_cublas_gemm(m, n, k, dt, label)
        print(f"{g['label']:50s} | {g['shape']:14s} | {g['tflops']:7.2f} TFLOPS")

    # FP8 _scaled_mm with FP32 accumulate (Locked cap is ~330.3 TFLOPS theoretical, ~220 TFLOPS practical)
    a8 = torch.randn((2048, 2048), device="cuda", dtype=torch.float16).to(torch.float8_e4m3fn)
    b8 = torch.randn((2048, 2048), device="cuda", dtype=torch.float16).to(torch.float8_e4m3fn).t()
    sa = torch.tensor(1.0, device="cuda", dtype=torch.float32)
    sb = torch.tensor(1.0, device="cuda", dtype=torch.float32)
    for _ in range(30):
        torch._scaled_mm(a8, b8, sa, sb, out_dtype=torch.bfloat16, use_fast_accum=False)
    torch.cuda.synchronize()
    s = torch.cuda.Event(enable_timing=True); e = torch.cuda.Event(enable_timing=True)
    s.record()
    for _ in range(80):
        torch._scaled_mm(a8, b8, sa, sb, out_dtype=torch.bfloat16, use_fast_accum=False)
    e.record()
    torch.cuda.synchronize()
    fp8_ms = s.elapsed_time(e) / 80.0
    fp8_tf = (2.0 * 2048 ** 3) / (fp8_ms * 1e-3) / 1e12
    print(f"{'FP8  (FP32 acc, torch._scaled_mm)':50s} | {'2048x2048x2048':14s} | {fp8_tf:7.2f} TFLOPS")
    print("=" * 78)


if __name__ == "__main__":
    main()
