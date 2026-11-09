#requires -Version 7.4
$ErrorActionPreference='Stop'
$root=Join-Path $env:TEMP "ora-director-$([guid]::NewGuid())"
$repo=Join-Path $root repo
New-Item -ItemType Directory "$repo/experiments" -Force | Out-Null
git init -q -b fixture $repo
'inert fixture' | Set-Content "$repo/experiments/executed_heredity.py"
git -C $repo add -- .
git -C $repo -c user.name=Fixture -c user.email=fixture@example.invalid commit -qm fixture
if ($LASTEXITCODE) {throw 'Cannot create fixture'}
$head=git -C $repo rev-parse HEAD
$blob=git -C $repo rev-parse HEAD:experiments/executed_heredity.py
$script=Join-Path $PSScriptRoot Invoke-OraCodex.ps1
$fake=Join-Path $PSScriptRoot Fake-DirectorWorker.ps1
function Setup($scenario) {
    @{worktree=$repo;branch='fixture';lease="$root/lease";mode='probe';directorEnabled=$true;
      fakeScenario=$scenario;timeoutSeconds=20;retryMinutes=0;intervalMinutes=0} |
      ConvertTo-Json | Set-Content "$root/config.json"
    @{status='ready';task=@{id='ORA-DIRECTOR';stage='execute';item='CHECKPOINT-HEAD';
      head=$head;expected=$head;blob=$blob;turn=1}}|ConvertTo-Json -Depth 5|Set-Content "$root/status.json"
}
function Step($status,$stage) {
    & $script -StateRoot $root -FakeWorker $fake
    $s=Get-Content -Raw "$root/status.json"|ConvertFrom-Json
    if($s.status -ne $status -or $s.task.stage -ne $stage){throw "Expected $status/$stage; got $($s.status)/$($s.task.stage)"}
}
Setup normal
Step ready review
Step ready direct
Step ready execute
Step ready review
Step ready direct
Step parked direct
$count=@(Get-ChildItem "$root/runs" -Filter '*.receipt.json').Count
Step parked direct
if(@(Get-ChildItem "$root/runs" -Filter '*.receipt.json').Count -ne $count){throw 'PARKED relaunched'}
Setup normal
Step ready review
$s=Get-Content -Raw "$root/status.json"|ConvertFrom-Json
$s.task.evidence="$root/config.json"
$s.task.evidenceSha256=(Get-FileHash "$root/config.json").Hash.ToLowerInvariant()
$s|ConvertTo-Json -Depth 8|Set-Content "$root/status.json"
Step parked review
Setup invented
Step parked execute
Setup forged
Step ready review
Step ready direct
Step parked direct
Setup normal
New-Item -ItemType File "$root/STOP"|Out-Null
Step ready execute
Remove-Item "$root/STOP"
Setup normal
$s=Get-Content -Raw "$root/status.json"|ConvertFrom-Json
$s.task.head='0'*40
$s|ConvertTo-Json -Depth 5|Set-Content "$root/status.json"
Step parked execute
"PASS fake loop, invented evidence, forbidden decision, foreign evidence path, STOP, wrong HEAD, and parked suppression. $root"
. "$PSScriptRoot/OraDirector.ps1"
$e=@{type='command_execution';exit_code=0;
 command='"C:\fixture\pwsh.exe" -Command ''git rev-parse HEAD; git rev-parse HEAD:experiments/executed_heredity.py''';
 aggregated_output="$head`n$blob"}
if(@(Get-OraGitOutputs $e).Count -ne 2){throw 'Exact compound readback rejected'}
$e.command=$e.command.Replace("git rev-parse HEAD;", "Write-Output '$head';")
if(@(Get-OraGitOutputs $e).Count){throw 'Forged shell output accepted'}
'PASS exact compound Git readback and forged shell rejection'
