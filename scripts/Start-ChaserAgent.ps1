# Start Chaser Agent on this Windows computer, with ChaseOS Cloud as its first reasoning route when a key is saved.
# On demand: registers no task, service or logon entry. -Stop stops it; -Open also opens the HUD.
#   powershell -ExecutionPolicy Bypass -File scripts\Start-ChaserAgent.ps1 [-Python <python.exe>] [-DataDir <folder>] [-Pack <pack.py>] [-Open|-Stop]
# Save the key once with scripts\Save-ChaseOSCloudKey.ps1. The service takes it out of its environment when it starts,
# so nothing it launches inherits it. Without a key it starts on the other routes and says Cloud is unavailable.
param(
    [string]$Python=(Join-Path (Split-Path -Parent $PSScriptRoot) '.venv\Scripts\python.exe'),
    [string]$DataDir=(Join-Path $env:LOCALAPPDATA 'ChaserAgent\data'),
    [int]$Port=8765,
    [string[]]$Pack=@(),
    [string]$KeyFile=(Join-Path $env:LOCALAPPDATA 'ChaserAgent\chaseos-cloud-key.dpapi'),
    [int]$MemoryLimitMb=1500,
    [switch]$Open,
    [switch]$Stop
)
$ErrorActionPreference='Stop'
$source=Split-Path -Parent $PSScriptRoot
function Test-Listening{$client=[Net.Sockets.TcpClient]::new();try{return $client.ConnectAsync('127.0.0.1',$Port).Wait(400)}catch{return $false}finally{$client.Dispose()}}
if($Stop){
    $owner=(Get-NetTCPConnection -LocalAddress 127.0.0.1 -LocalPort $Port -State Listen -ErrorAction SilentlyContinue).OwningProcess
    if($owner){Stop-Process -Id $owner -Confirm:$false;"Stopped Chaser Agent on port $Port."}else{'Chaser Agent is not running.'}
    exit 0
}
if(-not (Test-Path -LiteralPath $Python -PathType Leaf)){throw "No Python at $Python. Create the environment first: py -3.12 -m venv .venv; .venv\Scripts\python -m pip install -e ."}
if(-not (Test-Path -LiteralPath $DataDir)){
    # A private folder: current user, SYSTEM and Administrators only, as the service's start check requires.
    New-Item -ItemType Directory -Path $DataDir|Out-Null
    $acl=Get-Acl -LiteralPath $DataDir
    $acl.SetAccessRuleProtection($true,$false)
    foreach($rule in @($acl.Access)){[void]$acl.RemoveAccessRuleSpecific($rule)}
    foreach($sid in @([Security.Principal.WindowsIdentity]::GetCurrent().User,[Security.Principal.SecurityIdentifier]::new('S-1-5-18'),[Security.Principal.SecurityIdentifier]::new('S-1-5-32-544'))){
        $acl.AddAccessRule([Security.AccessControl.FileSystemAccessRule]::new($sid,'FullControl','ContainerInherit,ObjectInherit','None','Allow'))
    }
    Set-Acl -LiteralPath $DataDir -AclObject $acl
}
if(Test-Listening){"Chaser Agent is already on port $Port."}
else{
    $log=Join-Path $DataDir 'service.log'
    $arguments=@('-X','utf8','-m','chaser_agent.cli','serve','--data-dir',"`"$DataDir`"",'--port',$Port,'--memory-limit-mb',$MemoryLimitMb)
    foreach($item in $Pack){$arguments+=@('--pack',"`"$item`"")}
    $env:PYTHONUTF8='1'
    if(Test-Path -LiteralPath $KeyFile){
        $secure=Get-Content -Raw -LiteralPath $KeyFile|ConvertTo-SecureString
        $env:CHASEOS_CLOUD_KEY=[Net.NetworkCredential]::new('',$secure).Password
    }else{'No ChaseOS Cloud key is saved, so Chaser Agent starts without its Cloud route.'}
    try{Start-Process -FilePath $Python -ArgumentList $arguments -WorkingDirectory $source -WindowStyle Hidden -RedirectStandardOutput $log -RedirectStandardError ($log+'.err')|Out-Null}
    finally{Remove-Item Env:CHASEOS_CLOUD_KEY -ErrorAction SilentlyContinue}
    foreach($attempt in 1..120){if(Test-Listening){break};Start-Sleep -Milliseconds 500}
    if(-not (Test-Listening)){throw "Chaser Agent did not start. See $log.err"}
    "Chaser Agent is running on http://127.0.0.1:$Port/"
}
if($Open){& $Python -X utf8 -m chaser_agent.cli open --data-dir $DataDir --port $Port}
