# Finite catalog. Model output selects an ID; it never becomes an executable prompt.
$OraTasks = @{
    'CHECKPOINT-HEAD' = 'Run git rev-parse HEAD and report the exact SHA.'
    'FROZEN-BLOB' = 'Run git rev-parse HEAD:experiments/executed_heredity.py and report the exact Git blob.'
}
$OraDirectorStages = @('execute','review','direct')
function Get-OraDirectorPrompt($task) {
    $limits='Read-only. No writes, Worlds, seed access, native tests, network, workflows, pushes, merges, or protected runtime actions.'
    switch ($task.stage) {
        'execute' { "$limits Exact starting HEAD $($task.head). $($OraTasks[$task.item])" }
        'review' {
            $ref=if ($task.item -eq 'FROZEN-BLOB') {'HEAD:experiments/executed_heredity.py'} else {'HEAD'}
            "$limits Fresh independent review. Inspect local raw JSONL at $($task.evidence) and run exactly git rev-parse $ref as a standalone command. At HEAD $($task.head), verify the bounded objective $($task.item). Return the exact head and ACCEPT only if actual command/output evidence supports the claim; otherwise REJECT or UNKNOWN."
        }
        'direct' {
            if ($task.item -eq 'FROZEN-BLOB') {
                return "$limits Inspect verified review JSONL at $($task.evidence) for HEAD $($task.head). The approved pilot catalog is exhausted. Return PARK with the exact head."
            }
            "$limits Fresh research director. Inspect verified local review JSONL at $($task.evidence) and source checkpoint $($task.head). Ora issue 328 prioritizes verified ecological evidence and forbids automatic scientific execution. This is the one-time scheduler handoff acceptance check. If the raw review verdict is ACCEPT at the exact head, select FROZEN-BLOB to verify the immutable simulator blob through the next scheduled executor. Otherwise select PARK. Return only the structured decision. Model output does not grant permission."
        }
    }
}
function Get-OraDirectorDecision($task, $state, $receipt, $sourceOk) {
    # Every transition is fail-closed and finite. Stages do not trust arbitrary prose.
    if (!$sourceOk -or $state.after.dirty.Count -or $state.exitCode -ne 0 -or
        !$receipt.completed -or $receipt.failed -or !$state.session) { return }
    if ($task.stage -eq 'execute') {
        if (!$receipt.gitOutputs -or $task.expected -cnotin $receipt.gitOutputs) { return }
        return @{id='ORA-DIRECTOR';stage='review';item=$task.item;head=$task.head;
                 expected=$task.expected;evidence=$state.stdout}
    }
    try { $value=$receipt.message | ConvertFrom-Json -AsHashtable -ErrorAction Stop }
    catch { return }
    if ($value -isnot [System.Collections.IDictionary] -or $value.Count -ne 2 -or
        $value.head -cne $task.head) { return }
    if ($task.stage -eq 'review' -and $value.decision -ceq 'ACCEPT' -and
        $task.expected -cin $receipt.gitOutputs) {
        return @{id='ORA-DIRECTOR';stage='direct';item=$task.item;head=$task.head;
                 expected=$task.expected;evidence=$state.stdout}
    }
    if ($task.stage -eq 'direct' -and $task.item -eq 'CHECKPOINT-HEAD' -and $value.decision -ceq 'FROZEN-BLOB') {
        return @{id='ORA-DIRECTOR';stage='execute';item='FROZEN-BLOB';head=$task.head;
                 expected=$task.blob;evidence=$state.stdout}
    }
}

function Get-OraGitOutputs($item) {
    if ($item.type -cne 'command_execution' -or $item.exit_code -ne 0) { return }
    $command=[string]$item.command
    if ($command -cmatch '^"[^"]+pwsh[.]exe" -Command ''([^'']+)''$') {
        $command=$Matches[1]
    }
    $lines=@(([string]$item.aggregated_output).Trim() -split '\r?\n')
    if (@($lines | Where-Object { $_ -cnotmatch '^[0-9a-f]{40}$' }).Count) { return }
    switch -CaseSensitive ($command) {
        'git rev-parse HEAD' { if ($lines.Count -eq 1) { $lines } }
        'git rev-parse HEAD:experiments/executed_heredity.py' { if ($lines.Count -eq 1) { $lines } }
        'git rev-parse HEAD; git rev-parse HEAD:experiments/executed_heredity.py' {
            if ($lines.Count -eq 2) { $lines }
        }
    }
}
# Real qualification catalog, restricted to the isolated AL02 checkout.
$OraEngineering = @{
    'AL02-CONTROLLER-AUDIT' = 'Inspect tools/run_al02_campaign.py and tests/test_al02_continuation.py. Determine whether a controller-entry test drives the first independent review boundary at index 16 and prevents any custody call without a receipt. Report the missing or covered case with exact source references. Make no edits.'
    'AL02-CONTROLLER-TEST' = 'Implement a focused no-dispatch regression in tests/test_al02_continuation.py for actual run_next at index 16 with no prior batch review. Use disposable paths and a custody spy that fails if called. Do not call real custody or run any scientific code. Run python -B -m unittest discover -s tests -p test_al02_continuation.py. Leave only that file changed; the supervisor records the resulting diff.'
}
function Get-OraEngineeringPrompt($task) {
    $scope="Isolated AL02 qualification at HEAD $($task.head). No production writes, Worlds, launch or consent, network, pushes, merges, permissions, other agents or controllers. Preserve the frozen context list and scientific source."
    switch ($task.stage) {
        'execute' { "$scope $($OraEngineering[$task.item])" }
        'review' { "$scope Independent read-only review. Inspect the actual source and raw executor JSONL at $($task.evidence). For AL02-CONTROLLER-AUDIT, ACCEPT only if the audit accurately identifies a missing controller-entry test for the index-16 review boundary. For AL02-CONTROLLER-TEST, ACCEPT only if the diff adds that specific controller-entry regression and demonstrates no custody invocation. Otherwise REJECT or UNKNOWN. Return exact HEAD and verdict." }
        'direct' { "$scope Inspect the accepted reviewer JSONL at $($task.evidence), the actual current source and objective. Select AL02-CONTROLLER-TEST only if the first audit established that the index-16 regression is missing and that this bounded change addresses it. Otherwise PARK. Return exact HEAD and decision." }
    }
}
function Get-OraEngineeringDecision($task,$state,$receipt,$sourceOk) {
    if (!$sourceOk -or $state.exitCode -ne 0 -or !$receipt.completed -or
        $receipt.failed -or !$state.session) { return }
    $edit=$task.item -ceq 'AL02-CONTROLLER-TEST'
    if ($edit) {
        if ($state.after.dirty.Count -ne 1 -or
            $state.after.dirty[0] -cnotmatch '^ M tests/test_al02_continuation[.]py$') { return }
        if ($task.stage -ceq 'execute' -and !$receipt.continuationTests) { return }
    } elseif ($state.after.dirty.Count) { return }
    if ($task.stage -ceq 'execute') {
        return @{id='ORA-DIRECTOR';stage='review';item=$task.item;head=$task.head;
                 expected=$task.expected;evidence=$state.stdout;diffSha256=$state.diffSha256}
    }
    try { $value=$receipt.message | ConvertFrom-Json -AsHashtable -ErrorAction Stop }
    catch { return }
    if ($value.Count -ne 2 -or $value.head -cne $task.head) { return }
    if ($task.stage -ceq 'review' -and $value.decision -ceq 'ACCEPT' -and !$edit) {
        return @{id='ORA-DIRECTOR';stage='direct';item=$task.item;head=$task.head;
                 expected=$task.expected;evidence=$state.stdout}
    }
    if ($task.stage -ceq 'direct' -and !$edit -and $value.decision -ceq 'AL02-CONTROLLER-TEST') {
        return @{id='ORA-DIRECTOR';stage='execute';item=$value.decision;head=$task.head;
                 expected=$task.expected;evidence=$state.stdout}
    }
}
