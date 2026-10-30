/* Finite synthetic-only EKA transport. Uses the existing PILOT74 Windows Job
 * containment pattern; never accepts a command, World module or science grant.
 * Build-generated pins lock the sole interpreter and sole synthetic program.
 * Parent precharges four births before creating this guardian. */
#define WIN32_LEAN_AND_MEAN
#define _WIN32_WINNT 0x0A00
#include <windows.h>
#include <bcrypt.h>
#include <stdio.h>
#include <stdlib.h>
#include <wchar.h>
#include "eka1_probe_pins.h"
#pragma comment(lib,"bcrypt.lib")

static HANDLE child_job, done_event;
static ULONGLONG absolute_end;
static DWORD WINAPI watchdog(LPVOID unused) {
    ULONGLONG now=GetTickCount64(),stop=absolute_end-500; (void)unused;
    if(WaitForSingleObject(done_event,now>=stop?0:(DWORD)(stop-now))==WAIT_TIMEOUT){
        if(child_job) TerminateJobObject(child_job,124);
        TerminateProcess(GetCurrentProcess(),124);
    }
    return 0;
}
static int ledger_matches(HANDLE f){
    FILE_ID_INFO id;LARGE_INTEGER size,zero={0},position;BCRYPT_ALG_HANDLE a=NULL;BCRYPT_HASH_HANDLE h=NULL;
    ULONG len=0,got=0;PUCHAR object=NULL;UCHAR bytes[16384],digest[32];DWORD n;char hex[65];int i,ok=0;
    if(!GetFileInformationByHandleEx(f,FileIdInfo,&id,sizeof(id))||
       id.VolumeSerialNumber!=EKA_LEDGER_VOLUME||memcmp(id.FileId.Identifier,EKA_LEDGER_ID,16)||
       !GetFileSizeEx(f,&size)||size.QuadPart!=EKA_LEDGER_EXTENT||
       !SetFilePointerEx(f,zero,&position,FILE_CURRENT)||!SetFilePointerEx(f,zero,NULL,FILE_BEGIN))return 0;
    if(BCryptOpenAlgorithmProvider(&a,BCRYPT_SHA256_ALGORITHM,NULL,0)<0||
       BCryptGetProperty(a,BCRYPT_OBJECT_LENGTH,(PUCHAR)&len,sizeof(len),&got,0)<0)goto end;
    object=malloc(len);if(!object||BCryptCreateHash(a,&h,object,len,NULL,0,0)<0)goto end;
    for(;;){if(!ReadFile(f,bytes,sizeof(bytes),&n,NULL))goto end;if(!n)break;if(BCryptHashData(h,bytes,n,0)<0)goto end;}
    if(BCryptFinishHash(h,digest,32,0)<0)goto end;
    for(i=0;i<32;i++)sprintf_s(hex+i*2,65-i*2,"%02x",digest[i]);ok=!strcmp(hex,EKA_LEDGER_SHA);
end:
    if(h)BCryptDestroyHash(h);if(a)BCryptCloseAlgorithmProvider(a,0);free(object);
    if(!SetFilePointerEx(f,position,NULL,FILE_BEGIN))ok=0;return ok;
}
static HANDLE pinned(const WCHAR *path,const char *expected){
    HANDLE f=CreateFileW(path,GENERIC_READ,FILE_SHARE_READ,NULL,OPEN_EXISTING,FILE_FLAG_OPEN_REPARSE_POINT,NULL);
    BY_HANDLE_FILE_INFORMATION info; BCRYPT_ALG_HANDLE a=NULL; BCRYPT_HASH_HANDLE h=NULL;
    ULONG len=0,got=0; PUCHAR object=NULL; UCHAR bytes[16384],digest[32]; DWORD n; char hex[65]; int i,ok=0;
    if(f==INVALID_HANDLE_VALUE)return NULL;
    if(!GetFileInformationByHandle(f,&info)||info.nNumberOfLinks!=1||
       (info.dwFileAttributes&(FILE_ATTRIBUTE_REPARSE_POINT|FILE_ATTRIBUTE_DIRECTORY)))goto end;
    if(BCryptOpenAlgorithmProvider(&a,BCRYPT_SHA256_ALGORITHM,NULL,0)<0||
       BCryptGetProperty(a,BCRYPT_OBJECT_LENGTH,(PUCHAR)&len,sizeof(len),&got,0)<0)goto end;
    object=malloc(len);if(!object||BCryptCreateHash(a,&h,object,len,NULL,0,0)<0)goto end;
    for(;;){if(!ReadFile(f,bytes,sizeof(bytes),&n,NULL))goto end;if(!n)break;
        if(BCryptHashData(h,bytes,n,0)<0)goto end;}
    if(BCryptFinishHash(h,digest,32,0)<0)goto end;
    for(i=0;i<32;i++)sprintf_s(hex+i*2,65-i*2,"%02x",digest[i]);
    ok=!strcmp(hex,expected);
end:
    if(h)BCryptDestroyHash(h);if(a)BCryptCloseAlgorithmProvider(a,0);free(object);
    if(!ok){CloseHandle(f);return NULL;}return f; /* held against write/delete */
}

int wmain(int argc,WCHAR **argv){
    HANDLE watchdog_dll=NULL,raw=NULL,record=NULL,readout=NULL,writeout=NULL,nul=NULL,watch=NULL,python=NULL,program=NULL,owner=NULL,root=NULL,jobs[2];
    PROCESS_INFORMATION pi={0};STARTUPINFOEXW sx={0};SIZE_T attrn=0;BOOL attr_ready=FALSE;
    SECURITY_ATTRIBUTES sa={sizeof(sa),NULL,TRUE};HANDLE inherited[2];WCHAR command[4096];
    JOBOBJECT_EXTENDED_LIMIT_INFORMATION lim={0},observed={0};JOBOBJECT_BASIC_ACCOUNTING_INFORMATION usage={0};
    FILETIME times[4];DWORD code=125,available=0,n=0,written=0,desc_pid=0;UCHAR buffer[16384];HANDLE desc=NULL;ULONGLONG desc_birth=0;
    ULONGLONG received=0,retained=0,birth=0,began=GetTickCount64(),close_end;
    int cleanup_errors[32]={0},cleanup_count=0;int mode,reason=0,eof=0,overflow=0,error=0,leaked=0;char result[2048],cleanup_raw[256];int result_n,cleanup_offset,cleanup_i;
    if(argc!=10)return 125;
    mode=_wtoi(argv[1]);raw=(HANDLE)(uintptr_t)_wcstoui64(argv[2],NULL,10);
    record=(HANDLE)(uintptr_t)_wcstoui64(argv[3],NULL,10);absolute_end=_wcstoui64(argv[4],NULL,10);
    if(mode<0||mode>8||absolute_end<=began||absolute_end-began>8000||absolute_end>EKA_GLOBAL_END||wcscmp(argv[5],L"EKA-SYNTHETIC-ONLY-v1")||wcscmp(argv[8],EKA_SEAL))return 125;
    /* Native independent watchdog includes source checks, creation and drain. */
    done_event=CreateEventW(NULL,TRUE,FALSE,NULL);if(!done_event)return 125;
    watch=CreateThread(NULL,0,watchdog,NULL,0,NULL);if(!watch){CloseHandle(done_event);return 125;}
    {FILETIME t[4];ULONGLONG b;BOOL member=FALSE;owner=(HANDLE)(uintptr_t)_wcstoui64(argv[7],NULL,10);root=(HANDLE)(uintptr_t)_wcstoui64(argv[9],NULL,10);
     if(!IsProcessInJob(GetCurrentProcess(),root,&member)||!member){error=29;goto close;}
     if(GetProcessId(owner)!=EKA_OWNER_PID||WaitForSingleObject(owner,0)!=WAIT_TIMEOUT||
        !GetProcessTimes(owner,&t[0],&t[1],&t[2],&t[3])){error=24;goto close;}
     b=((ULONGLONG)t[0].dwHighDateTime<<32)|t[0].dwLowDateTime;
     if(b!=EKA_OWNER_BIRTH||!ledger_matches((HANDLE)(uintptr_t)_wcstoui64(argv[6],NULL,10))){error=25;goto close;}}
    {WCHAR marker[2048];HANDLE f;DWORD used;char line[96];int count;
     if(swprintf_s(marker,2048,L"%ls\\case-%d.consumed",EKA_MARKER_ROOT,mode)<0){error=26;goto close;}
     f=CreateFileW(marker,GENERIC_WRITE,0,NULL,CREATE_NEW,FILE_ATTRIBUTE_NORMAL,NULL);
     if(f==INVALID_HANDLE_VALUE){error=27;goto close;}
     count=sprintf_s(line,sizeof(line),"%lu %llu %d",GetCurrentProcessId(),began,mode);
     if(count<0||!WriteFile(f,line,(DWORD)count,&used,NULL)||used!=(DWORD)count||!FlushFileBuffers(f)){CloseHandle(f);error=28;goto close;}
     CloseHandle(f);}
    python=pinned(EKA_PYTHON,EKA_PYTHON_SHA);program=pinned(EKA_PROGRAM,EKA_PROGRAM_SHA);watchdog_dll=pinned(EKA_OWNER_DLL,EKA_OWNER_DLL_SHA);
    if(!python||!program||!watchdog_dll){error=1;goto close;}
    child_job=CreateJobObjectW(NULL,NULL);if(!child_job){error=2;goto close;}
    lim.BasicLimitInformation.LimitFlags=JOB_OBJECT_LIMIT_JOB_TIME|JOB_OBJECT_LIMIT_ACTIVE_PROCESS|
        JOB_OBJECT_LIMIT_JOB_MEMORY|JOB_OBJECT_LIMIT_PROCESS_MEMORY|JOB_OBJECT_LIMIT_KILL_ON_JOB_CLOSE;
    lim.BasicLimitInformation.PerJobUserTimeLimit.QuadPart=10000000; /* 1 user CPU second */
    lim.BasicLimitInformation.ActiveProcessLimit=mode==6?2:1;
    lim.ProcessMemoryLimit=64ULL*1024*1024;lim.JobMemoryLimit=128ULL*1024*1024;
    if(!SetInformationJobObject(child_job,JobObjectExtendedLimitInformation,&lim,sizeof(lim))||
       !QueryInformationJobObject(child_job,JobObjectExtendedLimitInformation,&observed,sizeof(observed),NULL)||
       observed.BasicLimitInformation.LimitFlags!=lim.BasicLimitInformation.LimitFlags||
       observed.BasicLimitInformation.PerJobUserTimeLimit.QuadPart!=lim.BasicLimitInformation.PerJobUserTimeLimit.QuadPart||
       observed.BasicLimitInformation.ActiveProcessLimit!=lim.BasicLimitInformation.ActiveProcessLimit||
       observed.ProcessMemoryLimit!=lim.ProcessMemoryLimit||observed.JobMemoryLimit!=lim.JobMemoryLimit){error=3;goto close;}
    {DWORD action=JOB_OBJECT_TERMINATE_AT_END_OF_JOB;if(!SetInformationJobObject(child_job,JobObjectEndOfJobTimeInformation,&action,sizeof(action))){error=4;goto close;}}
    if(!CreatePipe(&readout,&writeout,&sa,0)||!SetHandleInformation(readout,HANDLE_FLAG_INHERIT,0)){error=5;goto close;}
    nul=CreateFileW(L"NUL",GENERIC_READ,FILE_SHARE_READ|FILE_SHARE_WRITE,&sa,OPEN_EXISTING,0,NULL);
    if(nul==INVALID_HANDLE_VALUE){nul=NULL;error=6;goto close;}
    sx.StartupInfo.cb=sizeof(sx);sx.StartupInfo.dwFlags=STARTF_USESTDHANDLES;
    sx.StartupInfo.hStdInput=nul;sx.StartupInfo.hStdOutput=sx.StartupInfo.hStdError=writeout;
    InitializeProcThreadAttributeList(NULL,2,0,&attrn);sx.lpAttributeList=malloc(attrn);
    if(!sx.lpAttributeList||!InitializeProcThreadAttributeList(sx.lpAttributeList,2,0,&attrn)){error=7;goto close;}attr_ready=TRUE;
    inherited[0]=nul;inherited[1]=writeout;
    jobs[0]=root;jobs[1]=child_job;
    if(!UpdateProcThreadAttribute(sx.lpAttributeList,0,PROC_THREAD_ATTRIBUTE_JOB_LIST,jobs,sizeof(jobs),NULL,NULL)||
       !UpdateProcThreadAttribute(sx.lpAttributeList,0,PROC_THREAD_ATTRIBUTE_HANDLE_LIST,inherited,sizeof(inherited),NULL,NULL)){error=8;goto close;}
    if(swprintf_s(command,4096,L"\"%ls\" -I -S -B \"%ls\" %d \"%ls\"",mode==1?L"Z:\\EKA-NONEXISTENT\\refused.exe":EKA_PYTHON,EKA_PROGRAM,mode,EKA_OWNER_DLL)<0){error=9;goto close;}
    /* All descendants inherit both root Job and this private Job; no breakaway. */
    if(!CreateProcessW(NULL,command,NULL,NULL,TRUE,EXTENDED_STARTUPINFO_PRESENT|CREATE_SUSPENDED|CREATE_NO_WINDOW,
                       NULL,NULL,&sx.StartupInfo,&pi)){error=10;goto close;}
    if(!GetProcessTimes(pi.hProcess,&times[0],&times[1],&times[2],&times[3])){error=11;goto close;}
    birth=((ULONGLONG)times[0].dwHighDateTime<<32)|times[0].dwLowDateTime;
    {BOOL member=FALSE;if(!IsProcessInJob(pi.hProcess,child_job,&member)||!member){error=12;goto close;}}
    {char start_record[256];int count=sprintf_s(start_record,sizeof(start_record),"{\"schema\":\"EKA-NATIVE-CHILD-START-v1\",\"pid\":%lu,\"birth\":\"%llu\",\"suspended\":true}\n",pi.dwProcessId,birth);
     if(count<0||!WriteFile(record,start_record,(DWORD)count,&written,NULL)||written!=(DWORD)count||!FlushFileBuffers(record)){error=30;goto close;}}
    if(GetTickCount64()>=absolute_end-3000||ResumeThread(pi.hThread)!=1){error=13;goto close;}
    CloseHandle(pi.hThread);pi.hThread=NULL;CloseHandle(writeout);writeout=NULL;
    if(mode==7)Sleep(20000); /* explicit blocked-guardian watchdog fixture */
    for(;;){
        BOOL alive=WaitForSingleObject(pi.hProcess,0)==WAIT_TIMEOUT;
        if(mode==6&&!desc){struct{DWORD assigned,listed;ULONG_PTR pids[4];} ids={0};DWORD i;
            if(!QueryInformationJobObject(child_job,JobObjectBasicProcessIdList,&ids,sizeof(ids),NULL)){error=31;break;}
            for(i=0;i<ids.listed&&i<4;i++)if(ids.pids[i]!=pi.dwProcessId){
                desc_pid=(DWORD)ids.pids[i];desc=OpenProcess(SYNCHRONIZE|PROCESS_QUERY_LIMITED_INFORMATION,FALSE,desc_pid);
                if(!desc||!GetProcessTimes(desc,&times[0],&times[1],&times[2],&times[3])){error=32;break;}
                desc_birth=((ULONGLONG)times[0].dwHighDateTime<<32)|times[0].dwLowDateTime;break;}
            if(error)break;}
        if(WaitForSingleObject(owner,0)!=WAIT_TIMEOUT){reason=4;TerminateJobObject(child_job,124);}
        if(GetTickCount64()>=absolute_end-3000){reason=1;TerminateJobObject(child_job,124);}
        if(!PeekNamedPipe(readout,NULL,0,NULL,&available,NULL)){
            if(GetLastError()==ERROR_BROKEN_PIPE){eof=1;break;}error=14;break;}
        if(available){DWORD count=available>sizeof(buffer)?sizeof(buffer):available;
            if(!ReadFile(readout,buffer,count,&n,NULL)){error=15;break;}received+=n;
            count=(DWORD)((65536-retained)<n?(65536-retained):n);
            if(count&&(!WriteFile(raw,buffer,count,&written,NULL)||written!=count)){error=16;break;}retained+=count;
            if(received>65536){overflow=1;reason=2;TerminateJobObject(child_job,124);}
        }else if(!alive){
            if(!QueryInformationJobObject(child_job,JobObjectBasicAccountingInformation,&usage,sizeof(usage),NULL)){error=17;break;}
            if(usage.ActiveProcesses){leaked=1;reason=3;TerminateJobObject(child_job,125);}
        }
        Sleep(1);
    }
close:
    {int primary_error=error;
    if(child_job)TerminateJobObject(child_job,125);
    close_end=GetTickCount64()+2500;if(close_end>absolute_end)close_end=absolute_end;
    if(child_job){do{if(!QueryInformationJobObject(child_job,JobObjectBasicAccountingInformation,&usage,sizeof(usage),NULL)){cleanup_errors[cleanup_count++]=18;if(!error)error=18;break;}
        if(!usage.ActiveProcesses)break;Sleep(1);}while(GetTickCount64()<close_end);
        if(usage.ActiveProcesses){cleanup_errors[cleanup_count++]=19;if(!error)error=19;}
        if(!QueryInformationJobObject(child_job,JobObjectExtendedLimitInformation,&observed,sizeof(observed),NULL)){cleanup_errors[cleanup_count++]=20;if(!error)error=20;}}
    if(pi.hProcess){if(WaitForSingleObject(pi.hProcess,0)!=WAIT_OBJECT_0){cleanup_errors[cleanup_count++]=21;if(!error)error=21;}GetExitCodeProcess(pi.hProcess,&code);}
    if(desc&&WaitForSingleObject(desc,0)!=WAIT_OBJECT_0){cleanup_errors[cleanup_count++]=33;if(!error)error=33;}
    if(writeout){CloseHandle(writeout);writeout=NULL;}
    if(!FlushFileBuffers(raw)){cleanup_errors[cleanup_count++]=22;if(!error)error=22;}
    if(primary_error)error=primary_error;
    cleanup_raw[0]='[';cleanup_offset=1;for(cleanup_i=0;cleanup_i<cleanup_count;cleanup_i++)cleanup_offset+=sprintf_s(cleanup_raw+cleanup_offset,sizeof(cleanup_raw)-cleanup_offset,"%s%d",cleanup_i?",":"",cleanup_errors[cleanup_i]);sprintf_s(cleanup_raw+cleanup_offset,sizeof(cleanup_raw)-cleanup_offset,"]");
    result_n=sprintf_s(result,sizeof(result),"{\"schema\":\"EKA-SYNTHETIC-NATIVE-v1\",\"mode\":%d,\"pid\":%lu,\"birth\":\"%llu\",\"exit_code\":%lu,\"error\":%d,\"cleanup_count\":%d,\"first_cleanup\":%d,\"cleanup\":%s,\"reason\":%d,\"eof\":%s,\"overflow\":%s,\"observed_descendant\":%s,\"desc_pid\":%lu,\"desc_birth\":\"%llu\",\"desc_signaled\":%s,\"received\":%llu,\"retained\":%llu,\"user_cpu_ticks\":%llu,\"peak_job_memory\":%llu,\"process_memory_cap\":%llu,\"job_memory_cap\":%llu,\"process_cap\":%lu,\"started_processes\":%lu,\"active\":%lu,\"elapsed_ms\":%llu}",mode,pi.dwProcessId,birth,code,error,cleanup_count,cleanup_count?cleanup_errors[0]:0,cleanup_raw,reason,eof?"true":"false",overflow?"true":"false",leaked?"true":"false",desc_pid,desc_birth,desc&&WaitForSingleObject(desc,0)==WAIT_OBJECT_0?"true":"false",received,retained,(ULONGLONG)usage.TotalUserTime.QuadPart,(ULONGLONG)observed.PeakJobMemoryUsed,(ULONGLONG)observed.ProcessMemoryLimit,(ULONGLONG)observed.JobMemoryLimit,observed.BasicLimitInformation.ActiveProcessLimit,usage.TotalProcesses,usage.ActiveProcesses,GetTickCount64()-began);
    if(result_n<0||!WriteFile(record,result,(DWORD)result_n,&written,NULL)||written!=(DWORD)result_n||!FlushFileBuffers(record)){if(!error)error=23;}
    if(pi.hThread)CloseHandle(pi.hThread);if(pi.hProcess)CloseHandle(pi.hProcess);if(desc)CloseHandle(desc);
    if(readout)CloseHandle(readout);if(nul)CloseHandle(nul);if(child_job){CloseHandle(child_job);child_job=NULL;}
    if(watchdog_dll)CloseHandle(watchdog_dll);if(python)CloseHandle(python);if(program)CloseHandle(program);
    if(attr_ready)DeleteProcThreadAttributeList(sx.lpAttributeList);free(sx.lpAttributeList);
    SetEvent(done_event);WaitForSingleObject(watch,1000);CloseHandle(watch);CloseHandle(done_event);
    return error?125:0;}
}
