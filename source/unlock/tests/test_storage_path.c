/* Pure parser checks: no firmware, storage, or GPU access. */
#include "../storage_path.h"
#include <stdio.h>
#include <stdlib.h>
#define CHECK(x) do {if(!(x)){fprintf(stderr,"failed line %d\n",__LINE__);return 1;}} while(0)
int main(void) {
  UINT8 bytes[128]={0};HARDDRIVE_DEVICE_PATH *hd=(VOID *)bytes;
  EFI_GUID wanted={0x12345678,0x1234,0x5678,{1,2,3,4,5,6,7,8}},zero={0};
  hd->Header.Type=MEDIA_DEVICE_PATH;hd->Header.SubType=MEDIA_HARDDRIVE_DP;
  hd->Header.Length[0]=sizeof(*hd);hd->MBRType=2;hd->SignatureType=2;hd->PartitionNumber=3;
  memcpy(hd->Signature,&wanted,sizeof(wanted));
  EFI_DEVICE_PATH_PROTOCOL *end=(VOID *)(bytes+sizeof(*hd));
  end->Type=END_DEVICE_PATH_TYPE;end->SubType=END_ENTIRE_DEVICE_PATH_SUBTYPE;end->Length[0]=4;
  CHECK(GuInternalEspPath((VOID *)bytes,sizeof(*hd)+4,&wanted,3));
  CHECK(GuInternalEspPath((VOID *)bytes,sizeof(*hd)+4,&wanted,0));
  CHECK(!GuInternalEspPath((VOID *)bytes,sizeof(*hd)+4,&wanted,1));
  CHECK(!GuInternalEspPath((VOID *)bytes,sizeof(*hd)+3,&wanted,3));
  CHECK(!GuInternalEspPath((VOID *)bytes,sizeof(bytes),&zero,3));
  hd->Signature[0]^=1;CHECK(!GuInternalEspPath((VOID *)bytes,sizeof(bytes),&wanted,3));hd->Signature[0]^=1;
  hd->SignatureType=1;CHECK(!GuInternalEspPath((VOID *)bytes,sizeof(bytes),&wanted,3));hd->SignatureType=2;
  end->SubType=END_INSTANCE_DEVICE_PATH_SUBTYPE;CHECK(!GuInternalEspPath((VOID *)bytes,sizeof(bytes),&wanted,3));
  end->SubType=END_ENTIRE_DEVICE_PATH_SUBTYPE;
  memcpy(bytes+sizeof(*hd),bytes,sizeof(*hd));
  end=(VOID *)(bytes+2*sizeof(*hd));end->Type=END_DEVICE_PATH_TYPE;end->SubType=END_ENTIRE_DEVICE_PATH_SUBTYPE;end->Length[0]=4;
  CHECK(!GuInternalEspPath((VOID *)bytes,sizeof(bytes),&wanted,3));
  puts("PASS: GPT volume path identity, zero GUID, truncation, ambiguity and mismatch checks");return 0;
}
