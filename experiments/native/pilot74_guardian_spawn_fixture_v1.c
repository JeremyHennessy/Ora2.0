/* NEW VM-free native fixture, SOURCE ONLY until independently granted.
   Includes the exact production spawn/watchdog/save_slot implementation.
   No finite guardian protocol, worker, World, module imports or old refusal.
   External owner must bind this binary/source/argv/Job/birth and full stdout.
   Compile as a separate artifact; never substitute for production guardian. */
#define wmain pilot74_retained_guardian_wmain
#include "pilot74_guardian_v1.c"
#undef wmain

static int fixture_emit(const char *s){
 DWORD n=(DWORD)strlen(s),written=0;HANDLE out=GetStdHandle(STD_OUTPUT_HANDLE);
 return out&&out!=INVALID_HANDLE_VALUE&&WriteFile(out,s,n,&written,NULL)&&written==n;
}
static int fixture_record(const char *stage,PROCESS_INFORMATION *pi,ULONGLONG creation,DWORD code){
 char b[1024];JOBOBJECT_BASIC_ACCOUNTING_INFORMATION u={0};BOOL known;
 known=QueryInformationJobObject(root_job,JobObjectBasicAccountingInformation,&u,sizeof(u),NULL);
 if(sprintf_s(b,sizeof(b),"{\"schema\":\"PILOT74-SPAWN-FIXTURE-v1\",\"stage\":\"%s\",\"fixture_pid\":%lu,\"fixture_birth\":\"%llu\",\"child_pid\":%lu,\"child_birth\":\"%llu\",\"child_exit\":%lu,\"root_usage_known\":%s,\"started_processes\":%lu,\"active_processes\":%lu,\"first_error\":%ld,\"spawn_error\":%lu,\"spawn_phase\":%lu,\"worlds\":0,\"finite_admission\":false}\n",stage,GetCurrentProcessId(),born(GetCurrentProcess()),pi->dwProcessId,creation,code,known?"true":"false",u.TotalProcesses,u.ActiveProcesses,first_error,spawn_error,spawn_phase)<0)return 0;
 return fixture_emit(b);
}
int wmain(int argc,WCHAR **argv){
 PROCESS_INFORMATION pi={0};HANDLE hs[2]={NULL,NULL},nul=NULL,out=NULL,watcher=NULL;
 SECURITY_ATTRIBUTES sa={sizeof(sa),NULL,TRUE};BOOL in=FALSE;DWORD received=0,code=125;
 ULONGLONG actual_birth=0,child_birth=0,now;WCHAR cmd[4096];Slot start={0};char *body=NULL,*saved=NULL;
 HANDLE birth_pipe;int success=0;
 /* Exact argv, actual original host handle/birth and empty root Job are external
    review requirements. Missing facts never imply a successful fixture. */
 if(argc!=7)return 125;
 root_job=(HANDLE)(uintptr_t)_wcstoui64(argv[1],NULL,10);
 t0=_wcstoui64(argv[2],NULL,10);deadline=t0+3600000;
 birth_pipe=(HANDLE)(uintptr_t)_wcstoui64(argv[3],NULL,10);
 if(!ReadFile(birth_pipe,&actual_birth,8,&received,NULL)||received!=8||!actual_birth||born(GetCurrentProcess())!=actual_birth)return 125;
 CloseHandle(birth_pipe);
 now=GetTickCount64();
 if(now<t0||now>=deadline-20000||!IsProcessInJob(GetCurrentProcess(),root_job,&in)||!in||!limits(root_job,2048ULL*MIB,2400,4,0))return 125;
 stop_event=CreateEventW(NULL,TRUE,FALSE,NULL);done_event=CreateEventW(NULL,TRUE,FALSE,NULL);
 if(!stop_event||!done_event)return 125;
 if(!wcscmp(argv[4],L"blocked-main-deadline")){
  /* A NEW short engineering deadline supplied to the SAME watchdog function.
     This proves no natural3600s or3580s transition and changes no pilot clock. */
  deadline=now+1000;
  if(!fixture_emit("{\"schema\":\"PILOT74-SPAWN-FIXTURE-v1\",\"stage\":\"short-watchdog-armed-main-blocking\",\"test_deadline_ms\":1000,\"natural_pilot_deadline_proven\":false,\"worlds\":0}\n"))return 125;
  watcher=CreateThread(NULL,0,watchdog,NULL,0,NULL);if(!watcher)return 125;
  Sleep(INFINITE);return 125; /* watchdog must terminate this root Job first */
 }
 if(wcscmp(argv[4],L"positive-spawn-custody"))return 125;
 watcher=CreateThread(NULL,0,watchdog,NULL,0,NULL);if(!watcher)return 125;
 active_job=CreateJobObjectW(NULL,NULL);
 if(!active_job||!limits(active_job,1024ULL*MIB,180,3,1)||!publish_stop(0,active_job))goto failed;
 nul=CreateFileW(L"NUL",GENERIC_READ,FILE_SHARE_READ|FILE_SHARE_WRITE,&sa,OPEN_EXISTING,0,NULL);
 if(nul==INVALID_HANDLE_VALUE)goto failed;
 if(!DuplicateHandle(GetCurrentProcess(),GetStdHandle(STD_OUTPUT_HANDLE),GetCurrentProcess(),&out,0,TRUE,DUPLICATE_SAME_ACCESS))goto failed;
 hs[0]=nul;hs[1]=out;
 if(swprintf_s(cmd,4096,L"\"%ls\" -I -S -c \"import os;os.write(1,b'P74_CHILD_OK\\n')\"",argv[5])<0)goto failed;
 if(!spawn(cmd,NULL,active_job,hs,2,&pi))goto failed;
 child_birth=spawn_birth;
 if(!child_birth||!spawn_root_known||!spawn_root_member||!spawn_child_known||!spawn_child_member)goto failed;
 if(!precharge(&start,argv[6],65536))goto failed;
 {Obj o={0};field(&o,"schema",quote("PILOT74-FIXTURE-REAL-SUSPENDED-COMMIT-v1"));field(&o,"pid",number(pi.dwProcessId));field(&o,"birth",quote(number(child_birth)));field(&o,"root_member",copy("true",4));field(&o,"child_member",copy("true",4));body=object(&o);}
 if(!body||(saved=save_slot(&start,body))==NULL)goto failed;
 /* Mandatory real production save_slot result AND original handles before resume. */
 if(WaitForSingleObject(pi.hProcess,0)!=WAIT_TIMEOUT||!GetExitCodeProcess(pi.hProcess,&code)||code!=STILL_ACTIVE)goto failed;
 if(!fixture_record("suspended-start-saved",&pi,child_birth,code)||!fixture_emit(saved)||!fixture_emit("\n")||!start_allowed(0)||ResumeThread(pi.hThread)!=1)goto failed;
 if(WaitForSingleObject(pi.hProcess,5000)!=WAIT_OBJECT_0||!GetExitCodeProcess(pi.hProcess,&code)||code||born(pi.hProcess)!=child_birth)goto failed;
 {JOBOBJECT_BASIC_ACCOUNTING_INFORMATION u={0};ULONGLONG until=GetTickCount64()+1000;
  for(;;){if(!QueryInformationJobObject(active_job,JobObjectBasicAccountingInformation,&u,sizeof(u),NULL))goto failed;if(!u.ActiveProcesses)break;if(GetTickCount64()>=until)goto failed;Sleep(1);}
  if(u.TotalProcesses!=1)goto failed;
 }
 if(!fixture_record("child-exited-original-handle",&pi,child_birth,code))goto failed;
 success=1;
failed:
 if(!success){DWORD first=GetLastError();fail(first,101);if(active_job)TerminateJobObject(active_job,125);if(pi.hProcess){TerminateProcess(pi.hProcess,125);WaitForSingleObject(pi.hProcess,1000);}fixture_record("incomplete-failure-available-facts",&pi,child_birth,code);}
 /* Final external EOF/root closure still required; no self-stopped claim. */
 if(pi.hThread)CloseHandle(pi.hThread);if(pi.hProcess)CloseHandle(pi.hProcess);
 if(out)CloseHandle(out);if(nul&&nul!=INVALID_HANDLE_VALUE)CloseHandle(nul);
 free(body);free(saved);
 if(!success)ExitProcess(125);
 ExitProcess(0);
}
