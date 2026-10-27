#pragma once
#include <Uefi.h>
#include <Protocol/DevicePath.h>
#include <string.h>

/* Caller must supply a readable firmware device path, bounded by MaxBytes. */
static BOOLEAN GuInternalEspPath(const EFI_DEVICE_PATH_PROTOCOL *path,UINTN max,const EFI_GUID *expected,UINT32 partition) {
  static const EFI_GUID zero={0,0,0,{0,0,0,0,0,0,0,0}};
  UINTN total=0,matches=0;
  if(!path||!expected||!memcmp(expected,&zero,sizeof(zero)))return FALSE;
  for(UINTN nodes=0;nodes<64 && total+4<=max;nodes++) {
    UINTN n=path->Length[0]+((UINTN)path->Length[1]<<8);
    if(n<4 || n>max-total)return FALSE;
    if(path->Type==MEDIA_DEVICE_PATH && path->SubType==MEDIA_HARDDRIVE_DP) {
      if(n!=sizeof(HARDDRIVE_DEVICE_PATH))return FALSE;
      const HARDDRIVE_DEVICE_PATH *hd=(const HARDDRIVE_DEVICE_PATH *)path;
      if(hd->MBRType!=2 || hd->SignatureType!=2 || (partition && hd->PartitionNumber!=partition) ||
         memcmp(hd->Signature,expected,sizeof(*expected)))return FALSE;
      matches++;
    }
    if(path->Type==END_DEVICE_PATH_TYPE)return matches==1 && n==4 && path->SubType==END_ENTIRE_DEVICE_PATH_SUBTYPE;
    total+=n;path=(const VOID *)((const UINT8 *)path+n);
  }
  return FALSE;
}
