/* Fixed little-endian DATA ABI; no command, path, limit or law fields. */
#ifndef EKA_RUNTIME_CAPSULE_V1_H
#define EKA_RUNTIME_CAPSULE_V1_H
#define EKA_CAPSULE_BYTES 478
#define EKA_CAPSULE_VERSION 1
#define EKA_CAPSULE_SOURCE_ONLY 1 /* Cannot be lifted by a runtime argument. */
#pragma pack(push,1)
typedef struct EKA_RUNTIME_CAPSULE_V1 {
    unsigned char magic[8];
    unsigned long version,bytes,mode,reserved;
    unsigned __int64 owner_pid,owner_birth,ledger_volume,ledger_extent,global_end,role_end;
    unsigned char ledger_id[16];
    char ledger_sha[65],registration_sha[65],assignment_sha[65],manifest_sha[65];
    char guardian_sha[65],binding_sha[65];
} EKA_RUNTIME_CAPSULE_V1;
#pragma pack(pop)
typedef char EKA_CAPSULE_SIZE_CHECK[(sizeof(EKA_RUNTIME_CAPSULE_V1)==EKA_CAPSULE_BYTES)?1:-1];
#endif
