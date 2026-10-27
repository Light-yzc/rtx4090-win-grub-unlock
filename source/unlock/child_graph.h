#pragma once
#include <Uefi.h>
#include <string.h>

/* CPU-only graph validator. A successful result is not an authorization to
   disconnect: firmware owner identities and code must also be reviewed. */
typedef struct {
  EFI_GUID protocol;
  EFI_HANDLE agent,controller;
  UINT32 attributes,count;
} GU_CHILD_EDGE;
typedef struct { EFI_HANDLE text,gop,edid; } GU_CHILD_AGENTS;

static inline BOOLEAN GuLocalChildGraph(const GU_CHILD_EDGE *e,UINTN n,EFI_HANDLE child,
                                 EFI_HANDLE console,GU_CHILD_AGENTS *agents) {
  static const EFI_GUID text={0x387477c2,0x69c7,0x11d2,{0x8e,0x39,0x00,0xa0,0xc9,0x69,0x72,0x3b}};
  static const EFI_GUID gop={0x9042a9de,0x23dc,0x4a38,{0x96,0xfb,0x7a,0xde,0xd0,0x80,0x51,0x6a}};
  static const EFI_GUID edid={0x1c0c34f6,0xd380,0x41fa,{0xa0,0x49,0x8a,0xd0,0x6c,0x1a,0x66,0xaa}};
  EFI_HANDLE text_driver=NULL,text_child=NULL,gop_driver=NULL,edid_driver=NULL;
  if(!e||!agents||!child||!console||child==console||n!=4)return FALSE;
  memset(agents,0,sizeof(*agents));
  for(UINTN i=0;i<n;i++) {
    if(!e[i].agent || e[i].count!=1)return FALSE;
    if(!memcmp(&e[i].protocol,&text,sizeof(text)) && e[i].attributes==EFI_OPEN_PROTOCOL_BY_DRIVER && e[i].controller==child && !text_driver)
      text_driver=e[i].agent;
    else if(!memcmp(&e[i].protocol,&text,sizeof(text)) && e[i].attributes==EFI_OPEN_PROTOCOL_BY_CHILD_CONTROLLER && e[i].controller==console && !text_child)
      text_child=e[i].agent;
    else if(!memcmp(&e[i].protocol,&gop,sizeof(gop)) && e[i].attributes==EFI_OPEN_PROTOCOL_BY_DRIVER && e[i].controller==child && !gop_driver)
      gop_driver=e[i].agent;
    else if(!memcmp(&e[i].protocol,&edid,sizeof(edid)) && e[i].attributes==EFI_OPEN_PROTOCOL_BY_DRIVER && e[i].controller==child && !edid_driver)
      edid_driver=e[i].agent;
    else return FALSE;
  }
  if(!text_driver||text_driver!=text_child||!gop_driver||!edid_driver||
     text_driver==gop_driver||text_driver==edid_driver||gop_driver==edid_driver)return FALSE;
  agents->text=text_driver;agents->gop=gop_driver;agents->edid=edid_driver;
  return TRUE;
}
