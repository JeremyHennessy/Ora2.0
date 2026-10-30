/* Native owner deadline: can terminate only the process loading this DLL.
 * No Python callback/GIL, process creation, World or arbitrary target API. */
#define WIN32_LEAN_AND_MEAN
#include <windows.h>
static HANDLE done_event,thread_handle;
static ULONGLONG deadline;
static LONG consumed;
static DWORD WINAPI wait_deadline(LPVOID unused){
    ULONGLONG now=GetTickCount64();(void)unused;
    if(WaitForSingleObject(done_event,now>=deadline?0:(DWORD)(deadline-now))==WAIT_TIMEOUT)
        TerminateProcess(GetCurrentProcess(),124);
    return 0;
}
__declspec(dllexport) BOOL EkaStartWatchdog(DWORD owner,ULONGLONG birth,ULONGLONG end){
    FILETIME t[4];ULONGLONG actual,now=GetTickCount64();
    if(owner!=GetCurrentProcessId()||end<=now||end-now>120000||
       !GetProcessTimes(GetCurrentProcess(),&t[0],&t[1],&t[2],&t[3]))return FALSE;
    actual=((ULONGLONG)t[0].dwHighDateTime<<32)|t[0].dwLowDateTime;
    if(actual!=birth||InterlockedCompareExchange(&consumed,1,0)!=0)return FALSE;
    deadline=end;done_event=CreateEventW(NULL,TRUE,FALSE,NULL);if(!done_event)return FALSE;
    thread_handle=CreateThread(NULL,0,wait_deadline,NULL,0,NULL);
    if(!thread_handle){CloseHandle(done_event);done_event=NULL;return FALSE;}return TRUE;
}
__declspec(dllexport) BOOL EkaStopWatchdog(void){
    if(!done_event||!thread_handle||!SetEvent(done_event))return FALSE;
    if(WaitForSingleObject(thread_handle,1000)!=WAIT_OBJECT_0)return FALSE;
    if(!CloseHandle(thread_handle))return FALSE;thread_handle=NULL;
    if(!CloseHandle(done_event))return FALSE;done_event=NULL;return TRUE;
}
