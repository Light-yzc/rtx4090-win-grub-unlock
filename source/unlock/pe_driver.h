/* SPDX-License-Identifier: MIT
 * Bounded loaded-image code view; adapted from the adjacent diagnostic probe. */
#pragma once
#include <Uefi.h>
static inline UINT16 GuPe16(const UINT8 *p){return (UINT16)(p[0]|((UINT16)p[1]<<8));}
static inline UINT32 GuPe32(const UINT8 *p){return (UINT32)p[0]|((UINT32)p[1]<<8)|((UINT32)p[2]<<16)|((UINT32)p[3]<<24);}
static inline BOOLEAN GuPeRange(UINTN n,UINTN off,UINTN size){return off<=n&&size<=n-off;}
static inline BOOLEAN GuLoadedCode(const UINT8 *p,UINTN n,UINT32 wanted_rva,UINT32 wanted_len) {
  UINTN pe,opt,table,i,count=0;UINT32 reloc,bytes,at=0;
  if(!p||n>16U*1024U*1024U||!GuPeRange(n,0,64)||GuPe16(p)!=0x5a4d)return FALSE;
  pe=GuPe32(p+60);
  if(!GuPeRange(n,pe,24)||GuPe32(p+pe)!=0x4550||GuPe16(p+pe+4)!=0x8664||
     !GuPe16(p+pe+6)||GuPe16(p+pe+6)>32)return FALSE;
  opt=pe+24;
  if(GuPe16(p+pe+20)<240||!GuPeRange(n,opt,GuPe16(p+pe+20))||GuPe16(p+opt)!=0x20b||
     GuPe32(p+opt+56)>n||GuPe32(p+opt+108)<6)return FALSE;
  table=opt+GuPe16(p+pe+20);
  if(!GuPeRange(n,table,(UINTN)GuPe16(p+pe+6)*40))return FALSE;
  for(i=0;i<GuPe16(p+pe+6);i++) {
    const UINT8 *s=p+table+i*40;
    if(GuPe32(s+36)&0x20000000U) {
      if(++count!=1 || GuPe32(s+12)!=wanted_rva || GuPe32(s+8)!=wanted_len ||
         !wanted_len || wanted_len>512U*1024U || !GuPeRange(n,wanted_rva,wanted_len))return FALSE;
    }
  }
  if(count!=1)return FALSE;
  reloc=GuPe32(p+opt+112+5*8);bytes=GuPe32(p+opt+116+5*8);
  if((!reloc)!=(!bytes)||!GuPeRange(n,reloc,bytes))return FALSE;
  while(at<bytes) {
    UINT32 page,block;UINTN j;
    if(bytes-at<8)return FALSE;
    page=GuPe32(p+reloc+at);block=GuPe32(p+reloc+at+4);
    if(block<8||(block&1)||block>bytes-at)return FALSE;
    for(j=8;j<block;j+=2) {
      UINT16 entry=GuPe16(p+reloc+at+j);UINT64 pos=(UINT64)page+(entry&0xfff);
      if((entry>>12)&&pos>=wanted_rva&&pos<(UINT64)wanted_rva+wanted_len)return FALSE;
    }
    at+=block;
  }
  return TRUE;
}
