#requires -Version 7.4
$ErrorActionPreference='Stop'
$root=Join-Path ([IO.Path]::GetTempPath()) "ora-supervisor-$([guid]::NewGuid())"
New-Item -ItemType Directory $root | Out-Null
$repo=Join-Path $root repo
git init -q -b fixture $repo
git -C $repo -c user.name=Fixture -c user.email=fixture@example.invalid commit -qm baseline --allow-empty
if ($LASTEXITCODE) { throw 'fixture Git setup failed' }
$worker=Join-Path $PSScriptRoot 'Fake-Worker.ps1'
$controller=Join-Path $PSScriptRoot 'Invoke-OraCodex.ps1'
$config=@{worktree=$repo;branch='fixture';lease="$root/lease";mode='probe';timeoutSeconds=20;retryMinutes=0;intervalMinutes=0}
function Configure($scenario) {
 $config.fakeScenario=$scenario
 $config | ConvertTo-Json | Set-Content "$root/config.json"
 if (Test-Path "$root/status.json") { Remove-Item "$root/status.json" }
}
function Status { Get-Content -Raw "$root/status.json" | ConvertFrom-Json }
function Check($expected) { if ((Status).status -ne $expected) { throw "Expected $expected, got $((Status).status)" } }
Configure 'normal'
& $controller $root $worker
Check 'completed'
Configure 'interrupt'
& $controller $root $worker
Check 'interrupted'
& $controller $root $worker
Check 'completed'
if ((Status).attempts -ne 2) { throw 'Recovery did not use the second attempt' }
Configure 'rate'
& $controller $root $worker
Check 'cooldown'
$run=(Status).run
& $controller $root $worker
if ((Status).run -ne $run) { throw 'Cooldown launched again' }
Configure 'sleep'
$job=Start-ThreadJob { param($c,$r,$w) & $c $r $w } -ArgumentList $controller,$root,$worker
try {
 for ($i=0;$i -lt 100;$i++) {
  if ((Test-Path "$root/status.json") -and (Status).status -eq 'running') { break }
  Start-Sleep -Milliseconds 50
 }
 Check 'running'
 $run=(Status).run
 & $controller $root $worker
 if ((Status).run -ne $run) { throw 'Duplicate launch' }
 New-Item -ItemType File "$root/STOP" | Out-Null
 Receive-Job $job -Wait -ErrorAction Stop
 Check 'stopped'
 & $controller $root $worker
 if ((Status).run -ne $run) { throw 'STOP launched again' }
} finally { Remove-Job $job -Force }
Remove-Item "$root/STOP"
Configure 'partial'
& $controller $root $worker
Check 'review'
if (!(Test-Path "$repo/partial.txt")) { throw 'Partial work lost' }
"PASS completion, interruption/resume, rate-limit cooldown, duplicate, STOP, partial work. Receipts: $root"
