/* Copy this file to source/unlock/local/local_profile.h (gitignored)
 * and replace the all-zero placeholders with your machine's GPT partition GUIDs.
 *
 * Example for GPT Partition GUID a95cc6eb-64d0-47af-b0e8-9a1ac77c0a95 (Partition 3):
 *   #define KOH_WINDOWS_ESP_GUID 0xa95cc6eb,0x64d0,0x47af,{0xb0,0xe8,0x9a,0x1a,0xc7,0x7c,0x0a,0x95}
 *   #define KOH_WINDOWS_ESP_PARTITION 3
 *   #define KOH_UNLOCK_ESP_GUID 0xa95cc6eb,0x64d0,0x47af,{0xb0,0xe8,0x9a,0x1a,0xc7,0x7c,0x0a,0x95}
 */
#pragma once
#define KOH_WINDOWS_ESP_GUID 0,0,0,{0,0,0,0,0,0,0,0}
#define KOH_WINDOWS_ESP_PARTITION 3
#define KOH_UNLOCK_ESP_GUID 0,0,0,{0,0,0,0,0,0,0,0}

