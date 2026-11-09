#requires -Version 7.4
param([string]$StateRoot=$PSScriptRoot, [string]$FakeWorker)
$ErrorActionPreference='Stop'
$config=Get-Content -Raw "$StateRoot/config.json" | ConvertFrom-Json
if ($FakeWorker -and $StateRoot -eq $PSScriptRoot) { throw 'Fake worker requires an isolated state directory' }
if (Test-Path "$StateRoot/STOP") { return }
try { $gate=[IO.File]::Open("$StateRoot/controller.lock",'OpenOrCreate','ReadWrite','None') }
catch [IO.IOException] { return }
. (Join-Path $PSScriptRoot 'OraDirector.ps1')
function Save($value) {
    $value | ConvertTo-Json -Depth 10 | Set-Content "$StateRoot/status.tmp" -Encoding utf8
    for ($attempt=0; ; $attempt++) {
        try { [IO.File]::Move("$StateRoot/status.tmp","$StateRoot/status.json",$true); break }
        catch [IO.IOException] { if ($attempt -ge 9) { throw }; Start-Sleep -Milliseconds 50 }
    }
}
function Snapshot {
    $head=git -C $config.worktree rev-parse HEAD
    if ($LASTEXITCODE -ne 0) { throw 'Cannot verify worktree HEAD' }
    $branch=git -C $config.worktree branch --show-current
    if ($LASTEXITCODE -ne 0 -or $branch -cne $config.branch) { throw 'Unexpected branch' }
    $dirty=@(git -C $config.worktree status --porcelain=v1 --untracked-files=all)
    if ($LASTEXITCODE -ne 0) { throw 'Cannot verify worktree status' }
    @{head=$head; dirty=$dirty}
}
function Get-OraDiffHash {
    $diff=git -C $config.worktree diff --binary HEAD
    if ($LASTEXITCODE -ne 0) { throw 'Cannot verify candidate diff' }
    [Convert]::ToHexString([Security.Cryptography.SHA256]::HashData(
        [Text.Encoding]::UTF8.GetBytes(($diff -join "`n")))).ToLowerInvariant()
}
function Get-OraProtectedPaths($objective) {
    $hashes=@{}
    foreach ($path in $allowedPaths) {
        if ($path -cne $objective.path) {
            $hashes[$path]=(Get-FileHash -LiteralPath (Join-Path $config.worktree $path)).Hash
        }
    }
    $hashes
}
function Receipt($path) {
    $result=@{session=$null; completed=$false; failed=$false; gitOutputs=@()}
    if (Test-Path $path) {
        $stream=[IO.FileStream]::new($path,'Open','Read','ReadWrite')
        $reader=[IO.StreamReader]::new($stream)
        try { while ($null -ne ($line=$reader.ReadLine())) {
            try { $event=$line | ConvertFrom-Json -AsHashtable -ErrorAction Stop } catch { continue }
            switch ($event.type) {
                'thread.started' { if ($event.thread_id -match '^[0-9a-f-]{36}$') { $result.session=$event.thread_id } }
                'turn.completed' { $result.completed=$true; $result.usage=$event.usage }
                'item.completed' {
                    if ($event.item.type -eq 'agent_message') { $result.message=$event.item.text }
                    $result.gitOutputs+=@(Get-OraGitOutputs $event.item)
                    if ($roadmap -and $event.item.type -ceq 'command_execution' -and $event.item.exit_code -eq 0 -and
                        $event.item.command.Contains($roadmap.test) -and
                        $event.item.aggregated_output -match '(?m)^OK\s*$' -and
                        $event.item.aggregated_output -match 'Ran [1-9][0-9]* test') { $result.roadmapTests=$true }
                    if ($event.item.type -ceq 'command_execution' -and $event.item.exit_code -eq 0 -and
                        $event.item.command -match 'python -B -m unittest discover -s tests -p test_al02_continuation[.]py' -and
                        $event.item.aggregated_output -match '(?m)^OK\s*$') { $result.continuationTests=$true }
                }
                'turn.failed' { $result.failed=$true; $result.failureText += [string]$event.error.message }
                'error' { $result.failed=$true; $result.failureText += [string]$event.message }
            }
        } } finally { $reader.Dispose() }
    }
    $result
}
$lease=$null
$closed=$true
try {
    $previous=if (Test-Path "$StateRoot/status.json") { Get-Content -Raw "$StateRoot/status.json" | ConvertFrom-Json -AsHashtable }
    if ($previous -and $previous.status -in @('launching','running')) {
        # A controller crash can leave an orphan worker. Never launch over it.
        $existing=if ($previous.workerPid) { Get-Process -Id $previous.workerPid -ErrorAction SilentlyContinue }
        if ($existing -and $existing.StartTime.ToUniversalTime().Ticks -eq $previous.workerBirth) { return }
        if ($previous.status -eq 'launching') { return } # Ambiguous launch window requires inspection.
        $oldOwner=Get-Process -Id $previous.ownerPid -ErrorAction SilentlyContinue
        if ($oldOwner -and $oldOwner.StartTime.ToUniversalTime().Ticks -eq $previous.ownerBirth) { return }
        if (Test-Path $config.lease) {
            try { $stale=Get-Content -Raw $config.lease | ConvertFrom-Json -AsHashtable } catch { return }
            if ($stale.supervisor -cne $StateRoot -or $stale.pid -ne $previous.ownerPid -or
                $stale.birth -ne $previous.ownerBirth) { return }
            Remove-Item -LiteralPath $config.lease
        }
        $previous.status='interrupted'
        $previous.session=(Receipt $previous.stdout).session ?? $previous.session
        $previous.nextUtc=[DateTimeOffset]::UtcNow.AddMinutes($config.retryMinutes).ToString('o')
        Save $previous
    }
    if ($previous -and ($previous.status -in @('parked','review','stopped') -or
        ($previous.nextUtc -and [DateTimeOffset]::Parse($previous.nextUtc) -gt [DateTimeOffset]::UtcNow))) { return }
    if (Test-Path "$StateRoot/STOP") { return }
    if (!$FakeWorker -and $config.mode -eq 'probe' -and
        @(Get-ChildItem "$StateRoot/runs" -Filter '*.receipt.json' -ErrorAction SilentlyContinue).Count -ge 2) { return }
    $before=Snapshot
    $task=$previous.task
    $director=$task.id -ceq 'ORA-DIRECTOR'
    $roadmapMode=$director -and $task.item -ceq 'ROADMAP'
    if ($roadmapMode) {
        if (!$config.engineeringQualification -or $FakeWorker -or
            $config.worktree -cne 'D:/OraLab/src/Ora2.0-director-qualification' -or
            $StateRoot -cne 'D:/OraLab/drafts/ora-director-cross-objective') { throw 'Roadmap isolation differs' }
        $roadmapPath=Join-Path $PSScriptRoot 'roadmap-al02.json'
        if ((Get-FileHash $roadmapPath).Hash -ine $config.roadmapSha256) { throw 'Roadmap identity differs' }
        $catalog=Get-Content -Raw $roadmapPath | ConvertFrom-Json -AsHashtable
        $expectedObjective=Get-OraEligibleObjective $catalog $task.accepted
        if (!$expectedObjective -or $task.objective -cne $expectedObjective) { throw 'Roadmap objective order differs' }
        $roadmap=$catalog.objectives[$task.objective]
        $roadmap.secondsPerTurn=$catalog.secondsPerTurn
        $roadmap.maxCorrections=$catalog.maxCorrections
        $roadmap.maxTurns=$catalog.maxTurns
        $allowedPaths=@($catalog.objectives.Values | ForEach-Object { $_.path })
        $allowedDirty=@($allowedPaths | ForEach-Object { " M $_" })
        $protected=Get-OraProtectedPaths $roadmap
        if ($config.timeoutSeconds -gt $roadmap.secondsPerTurn) { throw 'Roadmap turn budget differs' }
        if (@($before.dirty | Where-Object { $_ -cnotin $allowedDirty }).Count) {
            throw 'Roadmap source scope differs'
        }
        $observedDiff=Get-OraDiffHash
        if ($previous.status -eq 'interrupted') {
            $recovered=Receipt $previous.stdout
            $savedDiff=Join-Path $StateRoot "runs/$($previous.run).diff"
            if (!$previous.evidenceSha256 -or !$previous.diffSha256 -or !$previous.diffFileSha256 -or
                $observedDiff -cne $previous.diffSha256 -or
                $recovered.session -cne $previous.session -or $recovered.completed -or
                (Get-FileHash -LiteralPath $previous.stdout).Hash -ine $previous.evidenceSha256 -or
                (Get-FileHash -LiteralPath $savedDiff).Hash -ine $previous.diffFileSha256 -or
                !$previous.roadmapScopeOk -or !$previous.after -or $previous.after.head -cne $before.head) {
                Save @{status='parked';reason='Interrupted roadmap evidence or source cannot be reconciled';task=$task;source=$before;previousRun=$previous.run}
                return
            }
        } elseif ($observedDiff -cne $task.diffSha256) {
            throw 'Roadmap checkpoint diff differs'
        }
    }
    $engineering=$director -and $OraEngineering.ContainsKey([string]$task.item)
    $engineeringEdit=$engineering -and $task.item -ceq 'AL02-CONTROLLER-TEST'
    $engineeringReview=$engineeringEdit -and $task.stage -ceq 'review'
    if ($engineering -and (!$config.engineeringQualification -or
        $config.worktree -cne 'D:/OraLab/src/Ora2.0-director-qualification' -or
        $StateRoot -cne 'D:/OraLab/drafts/ora-director-qualification')) { throw 'Engineering isolation differs' }
    if ($engineeringReview) {
        $diff=git -C $config.worktree diff --binary HEAD
        $hash=[Convert]::ToHexString([Security.Cryptography.SHA256]::HashData(
            [Text.Encoding]::UTF8.GetBytes(($diff -join "`n")))).ToLowerInvariant()
        if ($LASTEXITCODE -ne 0 -or $hash -cne $task.diffSha256) { throw 'Reviewed diff differs' }
    }
    if ($director -and (!$config.directorEnabled -or ($previous.status -ne 'ready' -and !($roadmapMode -and $previous.status -eq 'interrupted' -and $previous.session -and $previous.attempts -lt 2)) -or
        $task.stage -cnotin $OraDirectorStages -or (!$roadmapMode -and !$engineering -and !$OraTasks.ContainsKey([string]$task.item)) -or
        $task.head -cne $before.head -or ($before.dirty.Count -and !$engineeringReview -and !$roadmapMode) -or
        $task.turn -notin 1..$(if ($roadmapMode) {$roadmap.maxTurns} else {6}))) {
        Save @{status='parked';reason='Director scope, source, budget or restart mismatch';task=$task;source=$before}
        return
    }
    if ($director) {
        $task.evidenceRun=$task.evidenceRun ?? $previous.previousRun
        $blob=git -C $config.worktree rev-parse HEAD:experiments/executed_heredity.py
        if ($LASTEXITCODE -ne 0 -or $blob -cne $task.blob -or
            $task.expected -cne $(if ($task.item -eq 'FROZEN-BLOB') {$blob} else {$before.head}) -or
            ($task.turn -gt 1 -and ($task.evidenceRun -cnotmatch '^[0-9a-f-]{36}$' -or
             [IO.Path]::GetFullPath($task.evidence ?? '') -cne [IO.Path]::GetFullPath((Join-Path $StateRoot "runs/$($task.evidenceRun).jsonl")) -or
             !(Test-Path -LiteralPath $task.evidence) -or
             (Get-FileHash -LiteralPath $task.evidence).Hash.ToLowerInvariant() -cne $task.evidenceSha256))) {
            Save @{status='parked';reason='Director evidence identity mismatch';task=$task;source=$before}
            return
        }
    }
    if ($task -and !$director -and ($task.head -cne $before.head -or
        $task.id -cnotin @('AL02-ESCROW-V1-REVIEW','AL02-ONE-PAIR-REVIEW','AL02-WORKER-CLOSURE-REVIEW') -or $before.dirty.Count)) {
        Save @{status='review'; reason='READY task identity or clean source mismatch'; task=$task; source=$before}
        return
    }
    if ($previous -and $previous.status -eq 'interrupted' -and
        $before.head -cne (($previous.after ?? $previous.source).head)) {
        Save @{status='review'; reason='Interrupted session source HEAD changed'; source=$before}
        return
    }
    if (!$roadmapMode -and !$engineeringReview -and $before.dirty.Count -and (!$previous -or $previous.status -ne 'interrupted' -or !$previous.session)) {
        Save @{status='review'; reason='Unowned dirty worktree'; source=$before}
        return
    }
    if ((Get-PSDrive -Name ([IO.Path]::GetPathRoot($StateRoot).Substring(0,1))).Free -lt 1GB) { throw 'Insufficient disk space' }
    $logs=Join-Path $StateRoot 'runs'
    New-Item -ItemType Directory -Path $logs -Force | Out-Null
    if ((Get-ChildItem $logs -File | Measure-Object Length -Sum).Sum -ge 128MB) {
        Save @{status='parked';reason='Log budget reached';source=$before}; return
    }
    $leasePath=$config.lease
    try { $lease=[IO.File]::Open($leasePath,'CreateNew','Write','Read') }
    catch [IO.IOException] { return }
    $owner=Get-Process -Id $PID
    $identity=[Text.Encoding]::UTF8.GetBytes((@{pid=$PID; birth=$owner.StartTime.ToUniversalTime().Ticks; supervisor=$StateRoot} | ConvertTo-Json -Compress))
    $lease.Write($identity); $lease.Flush($true)
    $run=[guid]::NewGuid().ToString()
    $stdout=Join-Path $logs "$run.jsonl"
    $stderr=Join-Path $logs "$run.stderr"
    $resuming=$previous -and $previous.status -eq 'interrupted' -and $previous.session
    $prompt=if ($config.mode -eq 'probe') {
        'Read only. Report the current Git HEAD and the marker ORA_SUPERVISOR_PROBE_OK. Make no changes.'
    } else {
        'Use the latest verified Ora checkpoint and issue #328. The supervisor holds the exclusive source lease for this worker. Do not reacquire, remove or modify it. Perform one bounded safe source-only milestone in this worktree. First look for a reproduced AL02 defect or missing admitted source integration. Never treat a synthetic fixture as scientific evidence. No Worlds, scientific contexts, native qualification, workflows, push, merges, automation or protected runtime changes. Preserve existing partial work. If all useful work is blocked, say ORA_NO_SAFE_WORK and name the exact blocker. Do not start another controller.'
    }
    if ($director) {
        $prompt=if ($roadmapMode) { Get-OraRoadmapPrompt $task $roadmap } elseif ($engineering) { Get-OraEngineeringPrompt $task } else { Get-OraDirectorPrompt $task }
    } elseif ($task.id -ceq 'AL02-WORKER-CLOSURE-REVIEW') {
        $prompt="Read-only review of exact AL02 worker commit $($task.head). Inspect only the worker and tests. Do not run tests, workers or Worlds."
    } elseif ($task.id -ceq 'AL02-ONE-PAIR-REVIEW') {
        $prompt="Read-only review of AL02 one-pair source commit $($task.head). Inspect experiments/al02_one_pair.py, experiments/al02_one_pair_job.py and tests/test_al02_one_pair.py. No process smoke tests, World, source edits or scientific launch. Identify exact remaining conditional admission blockers. Never run the fixed context."
    } elseif ($task) {
        $prompt="Read-only independent review of AL02 escrow continuation commit $($task.head). Inspect only the two new files and relevant frozen methods. Run only python -B -S -m unittest tests.test_al02_depletion_producer -v. Do not construct or dispatch a World, edit files, or run historical tests. Report specific defects or scoped PASS."
    }
    if ($resuming -and $roadmapMode) {
        $prompt="Inspect saved partial diff $savedDiff and raw interrupted log $($previous.stdout). Preserve useful unfinished edits and reconcile them against the task. $prompt"
    }
    if ($resuming) { $prompt="Recover only the recorded interrupted work. Verify its partial changes first. $prompt" }
    $argsList=@('exec','--json','--color','never','-C',$config.worktree,'--sandbox','read-only')
    if ($config.mode -eq 'development' -and !$task) {
        $argsList=@('exec','--json','--color','never','-C',$config.worktree,'--approve-for-me')
    }
    if (($engineeringEdit -or $roadmapMode) -and $task.stage -ceq 'execute') {
        $argsList=@('exec','--json','--color','never','-C',$config.worktree,'--sandbox','workspace-write','-c','approval_policy="never"')
    }
    if ($director -and $task.stage -ne 'execute') {
        $schema=if ($roadmapMode) { if ($task.stage -ceq 'review') {'director-roadmap-review.schema.json'} else {'director-roadmap.schema.json'} } elseif ($task.stage -eq 'review') {'director-review.schema.json'} else {'director-plan.schema.json'}
        $argsList+=@('--output-schema',(Join-Path $PSScriptRoot $schema))
    }
    if ($resuming) { $argsList+=@('resume',$previous.session) }
    $argsList+=$prompt
    $info=[Diagnostics.ProcessStartInfo]::new()
    $info.FileName=$config.codex
    if ($FakeWorker) {
        $info.FileName=(Get-Process -Id $PID).Path
        $argsList=@('-NoProfile','-File',$FakeWorker,$config.fakeScenario,[string][bool]$resuming)
        if ($director) { $argsList+=@($task.stage,$task.item,$task.head,$task.expected) }
    }
    foreach ($arg in $argsList) { $info.ArgumentList.Add($arg) }
    $info.WorkingDirectory=$config.worktree
    $info.UseShellExecute=$false
    $info.CreateNoWindow=$true
    $info.RedirectStandardOutput=$true
    $info.RedirectStandardError=$true
    $state=@{status='launching';run=$run;task=$task;ownerPid=$PID;ownerBirth=$owner.StartTime.ToUniversalTime().Ticks;source=$before;stdout=$stdout;stderr=$stderr;
             session=if ($resuming) {$previous.session}; attempts=if ($previous -and $previous.status -eq 'interrupted') {1+[int]$previous.attempts} else {1};
             heartbeat=[DateTimeOffset]::UtcNow.ToString('o')}
    if ($engineering -or $roadmapMode) { $state.prompt=$prompt }
    if ($roadmapMode -and $task.stage -ceq 'execute' -and !$resuming) {
        $task.backup=Join-Path $logs "$run.before.py"
        Copy-Item -LiteralPath (Join-Path $config.worktree $roadmap.path) -Destination $task.backup
    }
    Save $state
    if (Test-Path "$StateRoot/STOP") { $state.status='stopped'; Save $state; return }
    $out=[IO.FileStream]::new($stdout,'CreateNew','Write','ReadWrite',1)
    $err=[IO.FileStream]::new($stderr,'CreateNew','Write','ReadWrite',1)
    $worker=$null
    try {
        $worker=[Diagnostics.Process]::Start($info)
        $closed=$false
        $state.workerPid=$worker.Id
        $state.workerBirth=$worker.StartTime.ToUniversalTime().Ticks
        $state.status='running'; Save $state
        $copyOut=$worker.StandardOutput.BaseStream.CopyToAsync($out)
        $copyErr=$worker.StandardError.BaseStream.CopyToAsync($err)
        $timer=[Diagnostics.Stopwatch]::StartNew()
        $peak=0L
        while (!$worker.WaitForExit(1000)) {
            $worker.Refresh()
            $peak=[Math]::Max($peak,$worker.WorkingSet64)
            if ($timer.Elapsed.TotalSeconds -ge $config.timeoutSeconds -or ($out.Length+$err.Length) -ge 8MB -or
                $peak -ge 1GB -or $worker.TotalProcessorTime.TotalSeconds -ge 180) {
                $state.terminated='Time, log, worker memory or worker CPU threshold'
                $worker.Kill($true)
                if (!$worker.WaitForExit(10000)) { throw 'Worker closure not confirmed' }
                break
            }
            if ($timer.Elapsed.Seconds % 15 -eq 0) {
                $state.session=(Receipt $stdout).session ?? $state.session
                $state.heartbeat=[DateTimeOffset]::UtcNow.ToString('o'); Save $state
            }
        }
        if (![Threading.Tasks.Task]::WaitAll(@($copyOut,$copyErr),10000)) { throw 'Worker output did not close' }
        $closed=$true
        $state.exitCode=$worker.ExitCode
        try { $state.cpuSeconds=$worker.TotalProcessorTime.TotalSeconds }
        catch { $state.cpuTelemetryError=$_.Exception.Message }
        $state.sampledPeakWorkingSet=$peak
    } catch {
        if ($worker -and !$worker.HasExited) {
            $worker.Kill($true)
            [void]$worker.WaitForExit(10000)
        }
        throw
    } finally {
        $out.Dispose(); $err.Dispose()
        if ($worker) { $worker.Dispose() }
    }
    $receipt=Receipt $stdout
    $state.session=$receipt.session ?? $state.session
    $state.usage=$receipt.usage
    $state.after=Snapshot
    $state.sourceChanged=($before.head -cne $state.after.head -or $state.after.dirty.Count -gt 0)
    $ratePattern='rate limit|rate_limit|usage limit|insufficient_quota|out of credits|HTTP 429'
    $rate=$receipt.failureText -match $ratePattern -or
        ($state.exitCode -ne 0 -and (Select-String -LiteralPath $stderr -Pattern $ratePattern -Quiet))
    $state.cooldowns=if ($rate) {1+[int]$previous.cooldowns} else {0}
    $state.status=if (Test-Path "$StateRoot/STOP") {'stopped'}
        elseif ($rate -and $state.cooldowns -ge 3) {'parked'}
        elseif ($rate) {'cooldown'}
        elseif ($state.exitCode -eq 0 -and $receipt.completed -and !$receipt.failed -and $state.session) {
            if ($task) {'parked'}
            elseif ($receipt.message -match '(?m)^ORA_NO_SAFE_WORK\b') {'parked'}
            elseif ($state.after.dirty.Count) {'review'}
            elseif ($config.mode -eq 'development' -and !$state.sourceChanged) {'parked'}
            else {'completed'}
        } elseif ($state.attempts -ge 2) {'parked'} else {'interrupted'}
    $minutes=if ($rate) {120*$state.cooldowns} elseif ($state.status -eq 'interrupted') {$config.retryMinutes} else {$config.intervalMinutes}
    $state.nextUtc=[DateTimeOffset]::UtcNow.AddMinutes($minutes).ToString('o')
    $state.heartbeat=[DateTimeOffset]::UtcNow.ToString('o')
    if ($director) {
        if ($state.status -eq 'interrupted' -and (!$roadmapMode -or !$state.session)) { $state.status='parked' }
        if ($engineeringEdit -or $roadmapMode) {
            $diff=git -C $config.worktree diff --binary HEAD
            if ($LASTEXITCODE -ne 0) { throw 'Cannot record engineering diff' }
            $state.diffSha256=[Convert]::ToHexString([Security.Cryptography.SHA256]::HashData(
                [Text.Encoding]::UTF8.GetBytes(($diff -join "`n")))).ToLowerInvariant()
            $diff | Set-Content "$logs/$run.diff" -Encoding utf8
            if ($roadmapMode) {
                $state.diffFileSha256=(Get-FileHash "$logs/$run.diff").Hash.ToLowerInvariant()
                $state.roadmapScopeOk=(@($state.after.dirty | Where-Object { $_ -cnotin $allowedDirty }).Count -eq 0)
                foreach ($path in $protected.Keys) {
                    if ((Get-FileHash -LiteralPath (Join-Path $config.worktree $path)).Hash -cne $protected[$path]) {
                        $state.roadmapScopeOk=$false
                    }
                }
                if (!$state.roadmapScopeOk) {
                    $state.status='parked'
                    $state.reason='Roadmap write scope differs'
                }
            }
            if (($engineeringReview -or ($roadmapMode -and $task.stage -cne 'execute')) -and $state.diffSha256 -cne $task.diffSha256) {
                throw 'Reviewer changed the source'
            }
        }
        $state.evidenceSha256=(Get-FileHash -LiteralPath $stdout).Hash.ToLowerInvariant()
        $state | ConvertTo-Json -Depth 10 | Set-Content "$logs/$run.receipt.json" -Encoding utf8
        if ($state.status -eq 'parked' -and !$rate -and !(Test-Path "$StateRoot/STOP")) {
            $next=if ($roadmapMode) { Get-OraRoadmapDecision $task $state $receipt $roadmap $catalog } elseif ($engineering) {
                Get-OraEngineeringDecision $task $state $receipt ($state.after.head -ceq $task.head)
            } else {
                Get-OraDirectorDecision $task $state $receipt ($state.after.head -ceq $task.head)
            }
            if ($next -and $task.turn -lt $(if ($roadmapMode) {$roadmap.maxTurns} else {6})) {
                $next.turn=1+[int]$task.turn
                $next.blob=$task.blob
                $next.evidenceSha256=$state.evidenceSha256
                $next.evidenceRun=$run
                Save @{status='ready';task=$next;previousRun=$run;nextUtc=if ($config.directorAcceptance) {[DateTimeOffset]::UtcNow.ToString('o')} else {$state.nextUtc}}
                return
            }
        }
        if ($roadmapMode -and $state.status -ceq 'parked' -and !$state.reason) {
            $state.reason=if ($task.turn -ge $roadmap.maxTurns) {'Roadmap turn budget exhausted'} else {'No verified eligible transition'}
        }
        Save $state
    } else {
        Save $state
        $state | ConvertTo-Json -Depth 10 | Set-Content "$logs/$run.receipt.json" -Encoding utf8
    }
} catch {
    if ($state) {
        $state.controllerError=$_.Exception.Message
        if ($closed) { $state.status='parked' }
        Save $state
    }
    throw
} finally {
    if ($lease) {
        $lease.Dispose()
        if ($closed) { Remove-Item -LiteralPath $leasePath }
    }
    $gate.Dispose()
}



