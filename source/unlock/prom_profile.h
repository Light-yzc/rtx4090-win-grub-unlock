#ifndef GU_PROM_PROFILE_H
#define GU_PROM_PROFILE_H
/* Derived from the bounded read-only CAP0003 on this machine. This pins the
 * captured live 1 MiB PROM view; the port itself remains unvalidated. */
#define GU_PROM_BAR_OFFSET 0x300000U
#define GU_PROM_VIEW_BYTES 0x100000U
#define GU_PROM_VIEW_SHA256 "df1098849b395d0399ab9eafb0a4108d8083884e612a016ad31bbde1628217b2"
#endif
