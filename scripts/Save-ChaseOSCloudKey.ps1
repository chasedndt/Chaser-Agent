# Save this computer's ChaseOS Cloud key for Chaser Agent. Run it yourself: it reads the key with no echo.
# The key is encrypted with Windows DPAPI for the current user only, so another account or computer can't read the file.
# Remove it with -Forget.
param([switch]$Forget,[string]$Path=(Join-Path $env:LOCALAPPDATA 'ChaserAgent\chaseos-cloud-key.dpapi'))
$ErrorActionPreference='Stop'
if($Forget){if(Test-Path -LiteralPath $Path){Remove-Item -LiteralPath $Path -Confirm:$false;'Removed the saved ChaseOS Cloud key.'}else{'No ChaseOS Cloud key is saved.'};exit 0}
$secure=Read-Host -AsSecureString 'Paste the ChaseOS Cloud key'
if($secure.Length -lt 8){throw 'That is too short to be a ChaseOS Cloud key.'}
New-Item -ItemType Directory -Force -Path (Split-Path -Parent $Path)|Out-Null
ConvertFrom-SecureString -SecureString $secure|Set-Content -LiteralPath $Path -Encoding ascii
'Saved. Chaser Agent uses it the next time it starts with scripts\Start-ChaserAgent.ps1.'
