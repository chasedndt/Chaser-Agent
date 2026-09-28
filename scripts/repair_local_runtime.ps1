# Explicit maintenance only. Never called by ordinary startup.
[CmdletBinding(SupportsShouldProcess, ConfirmImpact='High')]
param(
    [Parameter(Mandatory)][string]$RuntimePath,
    [switch]$RotateToken
)
$ErrorActionPreference = 'Stop'
$target = (Resolve-Path -LiteralPath $RuntimePath).ProviderPath.TrimEnd('\')
$allowed = 'E:\Projects\Chaser Agent\Local Runtime\2026-09-27-http-foundation'
if ($target -ne $allowed) { throw 'This maintenance receipt is scoped to the approved runtime only.' }
# Reject junctions/symlinks in every ancestor and descendant before changing ACLs.
$ancestor = Get-Item -LiteralPath $target -Force
while ($null -ne $ancestor) {
    if ($ancestor.Attributes -band [IO.FileAttributes]::ReparsePoint) { throw 'Reparse-point ancestor refused.' }
    $ancestor = $ancestor.Parent
}
$items = @((Get-Item -LiteralPath $target -Force))
$queue = [Collections.Generic.Queue[string]]::new()
$queue.Enqueue($target)
while ($queue.Count) {
    foreach ($item in Get-ChildItem -LiteralPath $queue.Dequeue() -Force) {
        if ($item.Attributes -band [IO.FileAttributes]::ReparsePoint) { throw 'Reparse-point child refused.' }
        $items += $item
        if ($item.PSIsContainer) { $queue.Enqueue($item.FullName) }
    }
}
if (-not $PSCmdlet.ShouldProcess($target, 'Restrict ACLs to current user, SYSTEM and Administrators; optionally rotate control token')) { return }
$sid = [Security.Principal.WindowsIdentity]::GetCurrent().User
$sections = [Security.AccessControl.AccessControlSections]::Access -bor [Security.AccessControl.AccessControlSections]::Owner -bor [Security.AccessControl.AccessControlSections]::Group
$before = @($items | ForEach-Object {
    [ordered]@{ path=$_.FullName; sddl=(Get-Acl -LiteralPath $_.FullName).GetSecurityDescriptorSddlForm($sections); sha256=if (-not $_.PSIsContainer) { (Get-FileHash -LiteralPath $_.FullName -Algorithm SHA256).Hash } else { $null } }
})
foreach ($item in $items) {
    $acl = Get-Acl -LiteralPath $item.FullName
    $acl.SetAccessRuleProtection($true, $false)
    foreach ($rule in @($acl.Access)) { [void]$acl.RemoveAccessRuleSpecific($rule) }
    $inheritance = if ($item.PSIsContainer) { [Security.AccessControl.InheritanceFlags]'ContainerInherit,ObjectInherit' } else { [Security.AccessControl.InheritanceFlags]::None }
    foreach ($principal in @($sid, [Security.Principal.SecurityIdentifier]::new('S-1-5-18'), [Security.Principal.SecurityIdentifier]::new('S-1-5-32-544'))) {
        $rule = [Security.AccessControl.FileSystemAccessRule]::new($principal, 'FullControl', $inheritance, 'None', 'Allow')
        $acl.AddAccessRule($rule)
    }
    Set-Acl -LiteralPath $item.FullName -AclObject $acl
}
$stamp = Get-Date -Format 'yyyyMMdd-HHmmss-fff'
$receiptPath = Join-Path $target "acl-maintenance-$stamp.json"
# Receipt contains ACL metadata and digests, never token contents. Root is now private.
$before | ConvertTo-Json -Depth 4 | Set-Content -LiteralPath $receiptPath -Encoding utf8
foreach ($record in $before) {
    if ($record.sha256 -and (Get-FileHash -LiteralPath $record.path -Algorithm SHA256).Hash -ne $record.sha256) { throw 'Artifact changed during repair; token was not rotated.' }
}
if ($RotateToken) {
    $bytes = [byte[]]::new(32)
    [Security.Cryptography.RandomNumberGenerator]::Fill($bytes)
    $token = [Convert]::ToHexString($bytes).ToLowerInvariant()
    [IO.File]::WriteAllText((Join-Path $target 'control-token'), $token, [Text.Encoding]::ASCII)
    $token = $null
    [Array]::Clear($bytes, 0, $bytes.Length)
}
[ordered]@{ status='acl_repaired'; paths_checked=$items.Count; existing_artifacts_preserved=$true; token_rotated=[bool]$RotateToken; private_receipt=$receiptPath } | ConvertTo-Json
