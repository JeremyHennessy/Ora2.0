$ErrorActionPreference='Stop'
New-Item -ItemType File -Path "$PSScriptRoot/STOP" -Force | Out-Null
Disable-ScheduledTask -TaskName 'OraCodexSupervisor' -TaskPath '\' | Out-Null
Write-Output 'STOP set. The active bounded session may finish. Future launches are disabled.'
