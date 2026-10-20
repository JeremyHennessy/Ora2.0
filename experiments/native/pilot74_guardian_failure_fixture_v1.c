/* New VM-free fault/interleaving qualification. Includes unchanged production
   helpers. Never invokes the production main or resumes the suspended child.
   External host must supply original birth, root Job and complete capture. */
#define wmain pilot74_retained_main
#include "pilot74_guardian_v1.c"
#undef wmain

static int emit_fact(const char *mode,PROCESS_INFORMATION *pi,DWORD code,int intact){
 char body[1024];DWORD written=0;JOBOBJECT_BASIC_ACCOUNTING_INFORMATION u={0};
 if(!QueryInformationJobObject(root_job,JobObjectBasicAccountingInformation,&u,sizeof(u),NULL))return 0;
 if(sprintf_s(body,sizeof(body),"{\"schema\":\"PILOT74-FAILURE-FIXTURE-v1\",\"mode\":\"%s\",\"child_pid\":%lu,\"child_birth\":\"%llu\",\"child_exit\":%lu,\"unrelated_child_intact\":%s,\"child_resumed\":false,\"started_processes\":%lu,\"active_processes\":%lu,\"worlds\":0}\n",mode,pi->dwProcessId,born(pi->hProcess),code,intact?"true":"false",u.TotalProcesses,u.ActiveProcesses)<0)return 0;
 return WriteFile(GetStdHandle(STD_OUTPUT_HANDLE),body,(DWORD)strlen(body),&written,NULL)&&written==(DWORD)strlen(body);
}

int wmain(int argc,WCHAR **argv){
 PROCESS_INFORMATION pi={0};HANDLE nul=NULL,out=NULL,old_job=NULL,hs[2];
 SECURITY_ATTRIBUTES sa={sizeof(sa),NULL,TRUE};ULONGLONG creation=0,until;
 HANDLE birth_pipe;DWORD received=0,code=259;BOOL in=FALSE;int ok=0,intact=0;
 WCHAR cmd[4096];Slot receipt={0};char *saved=NULL;
 JOBOBJECT_BASIC_ACCOUNTING_INFORMATION usage={0};
 if(argc!=7)return 125;
 root_job=(HANDLE)(uintptr_t)_wcstoui64(argv[1],NULL,10);
 t0=_wcstoui64(argv[2],NULL,10);deadline=t0+3600000;
 birth_pipe=(HANDLE)(uintptr_t)_wcstoui64(argv[3],NULL,10);
 if(!ReadFile(birth_pipe,&creation,8,&received,NULL)||received!=8||creation!=born(GetCurrentProcess()))return 125;
 CloseHandle(birth_pipe);
 if(!creation||!IsProcessInJob(GetCurrentProcess(),root_job,&in)||!in||!limits(root_job,2048ULL*MIB,2400,4,0))return 125;
 if(wcscmp(argv[4],L"receipt-write-refused")&&wcscmp(argv[4],L"stop-after-original-close"))return 125;
 stop_event=CreateEventW(NULL,TRUE,FALSE,NULL);done_event=CreateEventW(NULL,TRUE,FALSE,NULL);
 if(!stop_event||!done_event)return 125;
 if(!wcscmp(argv[4],L"stop-after-original-close")){
  old_job=CreateJobObjectW(NULL,NULL);
  if(!old_job||!limits(old_job,1024ULL*MIB,180,3,1)||!publish_stop(0,old_job))goto cleanup;
  /* Duplicate remains the sole owner after this close. Its old numeric handle
     may be reused; no assumption of actual reuse is part of the endpoint. */
  if(!CloseHandle(old_job))goto cleanup;old_job=NULL;
 }
 active_job=CreateJobObjectW(NULL,NULL);
 if(!active_job||!limits(active_job,1024ULL*MIB,180,3,1))goto cleanup;
 nul=CreateFileW(L"NUL",GENERIC_READ,FILE_SHARE_READ|FILE_SHARE_WRITE,&sa,OPEN_EXISTING,0,NULL);
 if(nul==INVALID_HANDLE_VALUE)goto cleanup;
 if(!DuplicateHandle(GetCurrentProcess(),GetStdHandle(STD_OUTPUT_HANDLE),GetCurrentProcess(),&out,0,TRUE,DUPLICATE_SAME_ACCESS))goto cleanup;
 hs[0]=nul;hs[1]=out;
 if(swprintf_s(cmd,4096,L"\"%ls\" -I -S -c \"import os;os.write(1,b'UNEXPECTED_CHILD_RESUME\\n')\"",argv[5])<0)goto cleanup;
 if(!spawn(cmd,NULL,active_job,hs,2,&pi)||!spawn_birth||!spawn_root_member||!spawn_child_member)goto cleanup;
 if(WaitForSingleObject(pi.hProcess,0)!=WAIT_TIMEOUT||!GetExitCodeProcess(pi.hProcess,&code)||code!=259)goto cleanup;
 if(!wcscmp(argv[4],L"receipt-write-refused")){
  /* Deliberate bounded write refusal, not a simulated disk failure. Actual
     production save_slot must reject a body larger than its precharged cap. */
  if(!precharge(&receipt,argv[6],1))goto cleanup;
  saved=save_slot(&receipt,"{\"deliberate\":true}");
  if(saved)goto cleanup;
  if(WaitForSingleObject(pi.hProcess,0)!=WAIT_TIMEOUT||!GetExitCodeProcess(pi.hProcess,&code)||code!=259)goto cleanup;
  if(!TerminateJobObject(active_job,125))goto cleanup;
 }else{
  stop_active(124); /* Stale published duplicate must target the OLD Job. */
  if(WaitForSingleObject(pi.hProcess,0)!=WAIT_TIMEOUT||!GetExitCodeProcess(pi.hProcess,&code)||code!=259)goto cleanup;
  if(!QueryInformationJobObject(active_job,JobObjectBasicAccountingInformation,&usage,sizeof(usage),NULL)||usage.ActiveProcesses!=1)goto cleanup;
  intact=1;
  if(!publish_stop(1,active_job))goto cleanup;
  stop_active(124); /* New publication must target the new child Job. */
 }
 if(WaitForSingleObject(pi.hProcess,5000)!=WAIT_OBJECT_0||!GetExitCodeProcess(pi.hProcess,&code)||born(pi.hProcess)!=spawn_birth)goto cleanup;
 if(code!=(!wcscmp(argv[4],L"receipt-write-refused")?125UL:124UL))goto cleanup;
 until=GetTickCount64()+1000;
 do{
  if(!QueryInformationJobObject(active_job,JobObjectBasicAccountingInformation,&usage,sizeof(usage),NULL))goto cleanup;
  if(!usage.ActiveProcesses)break;
  if(GetTickCount64()>=until)goto cleanup;
  Sleep(1);
 }while(1);
 if(usage.TotalProcesses!=1||!emit_fact(!wcscmp(argv[4],L"receipt-write-refused")?"receipt-write-refused":"stop-after-original-close",&pi,code,intact))goto cleanup;
 ok=1;
cleanup:
 /* Exact handles/Jobs only; no lookup by PID and no child resume anywhere. */
 if(active_job)TerminateJobObject(active_job,125);
 if(pi.hProcess){TerminateProcess(pi.hProcess,125);WaitForSingleObject(pi.hProcess,1000);}
 if(pi.hThread)CloseHandle(pi.hThread);if(pi.hProcess)CloseHandle(pi.hProcess);
 if(out)CloseHandle(out);if(nul&&nul!=INVALID_HANDLE_VALUE)CloseHandle(nul);
 if(old_job)CloseHandle(old_job);free(saved);
 ExitProcess(ok?0:125);
}
