param($Scenario,$Resuming,$Stage,$Item,$Head,$Expected)
@{type='thread.started';thread_id=[guid]::NewGuid().ToString()} | ConvertTo-Json -Compress
if ($Stage -in 'execute','review' -and $Scenario -ne 'invented') {
    $target=if ($Item -eq 'FROZEN-BLOB') {'HEAD:experiments/executed_heredity.py'} else {'HEAD'}
    $actual=git rev-parse $target
    @{type='item.completed';item=@{type='command_execution';command=('"C:\fixture\pwsh.exe" -Command ''git rev-parse {0}''' -f $target);exit_code=$LASTEXITCODE;aggregated_output=$actual}} | ConvertTo-Json -Compress
}
if ($Stage -in 'review','direct') {
    $decision=if ($Stage -eq 'review') {'ACCEPT'} elseif ($Item -eq 'FROZEN-BLOB') {'PARK'} elseif ($Scenario -eq 'forged') {'RUN-SCIENTIFIC-WORLD'} else {'FROZEN-BLOB'}
    $message=@{head=$Head;decision=$decision}|ConvertTo-Json -Compress
    @{type='item.completed';item=@{type='agent_message';text=$message}}|ConvertTo-Json -Compress
}
'{"type":"turn.completed","usage":{"input_tokens":1}}'

