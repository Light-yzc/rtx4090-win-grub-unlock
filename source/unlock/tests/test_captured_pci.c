/* Offline fixture audit only; never accesses a PCI device. */
#include "../checks.h"
#include <stdio.h>
#include <string.h>

int main(int argc,char **argv) {
  UINT32 captured[64],candidate[64]; GU_CAPS caps;
  if(argc!=2)return 2;
  FILE *f=fopen(argv[1],"rb");if(!f)return 2;
  if(fread(captured,1,sizeof(captured),f)!=sizeof(captured)||fgetc(f)!=EOF){fclose(f);return 2;}
  fclose(f);
  if(captured[0]!=GU_BOARD_ID || captured[11]!=GU_BOARD_SUBSYSTEM)return 3;
  memcpy(candidate,captured,sizeof(candidate));
  int original=GuCheckConfig(candidate,0,GU_BOARD_BUS,0,0,&caps);
  int observed=GuCheckObservedConfig(candidate,0,GU_BOARD_BUS,0,0,&caps);
  if(!observed || memcmp(candidate,captured,sizeof(candidate)))return 5;
  candidate[11]^=1;
  if(GuCheckObservedConfig(candidate,0,GU_BOARD_BUS,0,0,&caps))return 6;
  candidate[11]^=1;
  if(GuCheckObservedConfig(candidate,0,GU_BOARD_BUS+1,0,0,&caps))return 7;
  candidate[1]&=~2u;
  if(GuCheckObservedConfig(candidate,0,GU_BOARD_BUS,0,0,&caps))return 8;
  candidate[1]|=2u;
  candidate[1]&=~4u;
  int without_bme=GuCheckConfig(candidate,0,GU_BOARD_BUS,0,0,&caps);
  if(!GuCheckPostReleaseConfig(captured,candidate,0,GU_BOARD_BUS,0,0))return 9;
  for(unsigned mask=0;mask<4;mask++) {
    memcpy(candidate,captured,sizeof(candidate));candidate[1]=(candidate[1]&~7u)|mask;
    if(!GuCheckPostReleaseConfig(captured,candidate,0,GU_BOARD_BUS,0,0))return 13;
  }
  memcpy(candidate,captured,sizeof(candidate));candidate[1]&=~4u;
  for(unsigned i=0;i<64;i++) {
    if(i==1)continue;
    candidate[i]^=1;
    if(GuCheckPostReleaseConfig(captured,candidate,0,GU_BOARD_BUS,0,0))return 14;
    candidate[i]^=1;
  }
  candidate[1]&=~2u;
  if(!GuCheckPostReleaseConfig(captured,candidate,0,GU_BOARD_BUS,0,0))return 10;
  candidate[4]^=0x1000000u;
  if(GuCheckPostReleaseConfig(captured,candidate,0,GU_BOARD_BUS,0,0))return 11;
  candidate[4]^=0x1000000u;
  candidate[1]|=4u;
  if(GuCheckPostReleaseConfig(captured,candidate,0,GU_BOARD_BUS,0,0))return 12;
  candidate[1]&=~4u;
  printf("captured=%s; hypothetical BME-cleared=%s; pm=%x pcie=%x msi=%x msix=%x\n",
    original?"accepted":"rejected",without_bme?"accepted":"rejected",caps.pm,caps.pcie,caps.msi,caps.msix);
  if(original || !without_bme)return 4;
  /* This is a calculation on a copied array, not an instruction to clear BME. */
  return 0;
}
