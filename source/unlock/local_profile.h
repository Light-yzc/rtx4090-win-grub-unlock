/* Public inert default; local reviewed GUID required for execution.
 * Copy local_profile.example.h to local/local_profile.h (gitignored) and
 * fill in your reviewed partition GUIDs before building with --enable-experiment.
 */
#pragma once
#ifdef KOH_HOST_TEST
#define KOH_WINDOWS_ESP_GUID 0xdeadbeef,0x1111,0x2222,{8,7,6,5,4,3,2,1}
#define KOH_WINDOWS_ESP_PARTITION 3
#define KOH_UNLOCK_ESP_GUID 0x12345678,0x1234,0x5678,{1,2,3,4,5,6,7,8}
#elif defined(__has_include) && __has_include("local/local_profile.h")
#include "local/local_profile.h"
#else
#define KOH_WINDOWS_ESP_GUID 0,0,0,{0,0,0,0,0,0,0,0}
/* Observed active Intel SSD Windows ESP is GPT partition 3. */
#define KOH_WINDOWS_ESP_PARTITION 3
/* Dedicated or shared unlock asset/log GPT partition GUID. */
#define KOH_UNLOCK_ESP_GUID 0,0,0,{0,0,0,0,0,0,0,0}
#endif
