param($Scenario,$Resuming)
'{"type":"thread.started","thread_id":"11111111-1111-4111-8111-111111111111"}'
if ($Scenario -eq 'interrupt' -and $Resuming -ne 'True') { exit 7 }
if ($Scenario -eq 'rate') { [Console]::Error.WriteLine('HTTP 429 rate limit'); exit 1 }
if ($Scenario -eq 'sleep') { Start-Sleep -Seconds 5 }
if ($Scenario -eq 'normal') {
 '{"type":"item.completed","item":{"type":"command_execution","aggregated_output":"documentation about rate limit"}}'
}
if ($Scenario -eq 'partial') { Set-Content partial.txt 'fixture' }
'{"type":"turn.completed","usage":{"input_tokens":1,"output_tokens":1}}'
