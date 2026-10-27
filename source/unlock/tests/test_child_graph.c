/* Local ownership fixture with mutations. No firmware services are invoked. */
#include "../child_graph.h"
#include <stdio.h>
#define H(x) ((EFI_HANDLE)(UINTN)(x))
#define CHECK(x) do { if(!(x)){fprintf(stderr,"failed line %d\n",__LINE__);return 1;} } while(0)
int main(void) {
  EFI_GUID text={0x387477c2,0x69c7,0x11d2,{0x8e,0x39,0,0xa0,0xc9,0x69,0x72,0x3b}};
  EFI_GUID gop={0x9042a9de,0x23dc,0x4a38,{0x96,0xfb,0x7a,0xde,0xd0,0x80,0x51,0x6a}};
  EFI_GUID edid={0x1c0c34f6,0xd380,0x41fa,{0xa0,0x49,0x8a,0xd0,0x6c,0x1a,0x66,0xaa}};
  GU_CHILD_EDGE e[5]={{text,H(311),H(413),16,1},{text,H(311),H(314),8,1},
                       {gop,H(316),H(413),16,1},{edid,H(132),H(413),16,1}};
  GU_CHILD_AGENTS a;
  CHECK(GuLocalChildGraph(e,4,H(413),H(314),&a));
  CHECK(a.text==H(311)&&a.gop==H(316)&&a.edid==H(132));
  CHECK(!GuLocalChildGraph(e,3,H(413),H(314),&a));
  CHECK(!GuLocalChildGraph(e,5,H(413),H(314),&a));
  e[1].agent=H(999);CHECK(!GuLocalChildGraph(e,4,H(413),H(314),&a));e[1].agent=H(311);
  e[3].agent=H(316);CHECK(!GuLocalChildGraph(e,4,H(413),H(314),&a));e[3].agent=H(132);
  e[3].count=2;CHECK(!GuLocalChildGraph(e,4,H(413),H(314),&a));e[3].count=1;
  e[2].protocol=text;CHECK(!GuLocalChildGraph(e,4,H(413),H(314),&a));
  puts("PASS: local child text/GOP/EDID ownership pattern and mutation cases");return 0;
}
