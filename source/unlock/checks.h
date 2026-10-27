#pragma once

#include "port.h"

typedef struct {
  UINT16 pm, pcie, msi, msix;
  UINT8 pcie_version;
} GU_CAPS;

/* Config is a complete, CPU-owned 256-byte snapshot. Out is cleared on failure. */
BOOLEAN GuCheckConfig(const UINT32 Config[64], UINTN Segment, UINTN Bus,
                      UINTN Device, UINTN Function, GU_CAPS *Out);
/* Read-only preflight validation only. It does not authorize a claim, DMA,
   firmware execution or modifying bus mastering on the real device. */
BOOLEAN GuCheckObservedConfig(const UINT32 Config[64], UINTN Segment, UINTN Bus,
                              UINTN Device, UINTN Function, GU_CAPS *Out);
/* Offline snapshot predicate. Call only after separate exclusive ownership and
   hardware BME-clear verification; this function itself changes no device. */
BOOLEAN GuCheckPostReleaseConfig(const UINT32 Initial[64],const UINT32 Current[64],
                                 UINTN Segment,UINTN Bus,UINTN Device,UINTN Function);

/* Path must point to readable memory through its terminator, up to MaxBytes.
   MaxBytes is a read bound, not necessarily the exact allocation length.
   Returns 1 for the Intel route, 2 for the RTX route, and 0 otherwise. */
int GuDisplayPath(const EFI_DEVICE_PATH_PROTOCOL *Path, UINTN MaxBytes);
