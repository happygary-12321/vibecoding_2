# Final Assignment 3 transcript refresh

Run this only after the final assistant response and your review have been
persisted to the session log. The current snapshot is historical and does not
include all later lint-review/alignment turns. This procedure has been prepared,
not executed as a final export.

From PowerShell in `D:\CodexCLI\vibecoding\HW2`, run the following.
It uses the existing manifest's exact session path; it does not search for or
substitute another session. It preserves the raw JSONL bytes and updates coverage
metadata. A missing file, incomplete JSON record, or mismatched session stops
before the snapshot is replaced.

```powershell
$ErrorActionPreference = 'Stop'
$manifestPath = (Resolve-Path -LiteralPath 'assign3/transcript/manifest.json').Path
$manifest = Get-Content -Raw -Encoding UTF8 -LiteralPath $manifestPath | ConvertFrom-Json
$sourcePath = (Resolve-Path -LiteralPath $manifest.source).Path
$snapshotPath = Join-Path (Split-Path $manifestPath) $manifest.snapshot
$raw = [IO.File]::ReadAllBytes($sourcePath)
$utf8 = New-Object Text.UTF8Encoding($false, $true)
$records = @($utf8.GetString($raw) -split "\r?\n" |
    Where-Object { $_.Trim().Length -gt 0 } |
    ForEach-Object { $_ | ConvertFrom-Json })
$meta = $records[0].payload
if ($records[0].type -ne 'session_meta' -or
    $meta.session_id -ne $manifest.session_id) {
    throw 'Session identity mismatch; keep the existing snapshot.'
}
[IO.File]::WriteAllBytes($snapshotPath, $raw)
$manifest.sha256 = (Get-FileHash -LiteralPath $snapshotPath -Algorithm SHA256).Hash.ToLowerInvariant()
$manifest.bytes = $raw.Length
$manifest.record_count = $records.Count
$manifest.first_timestamp = $records[0].timestamp
$manifest.last_timestamp = $records[-1].timestamp
$manifest.copied_utc = [DateTime]::UtcNow.ToString('o')
$manifest.byte_preserved = $true
$manifest.recorded_turn_models = @($records |
    Where-Object { $_.type -eq 'turn_context' } |
    ForEach-Object {
        [PSCustomObject]@{timestamp=$_.timestamp; model=$_.payload.model}
    })
$manifest.user_requests = @($records | ForEach-Object {
    if ($_.type -eq 'response_item' -and $_.payload.role -eq 'user') {
        $message = ($_.payload.content | ForEach-Object { $_.text }) -join ' '
        if ($message -and -not $message.StartsWith('<environment_context>')) {
            [PSCustomObject]@{
                timestamp=$_.timestamp
                opening=$message.Substring(0, [Math]::Min(200, $message.Length))
            }
        }
    }
})
$manifest.coverage = "Raw snapshot through $($manifest.last_timestamp); final review coverage requires manual confirmation."
$manifest.remaining = 'Confirm the final assistant response, final user review, and any other relevant Assignment 3 session are included.'
[IO.File]::WriteAllText($manifestPath, ($manifest | ConvertTo-Json -Depth 30) + "`n", $utf8)
Get-Item -LiteralPath $snapshotPath | Select-Object FullName, Length
Get-FileHash -LiteralPath $snapshotPath -Algorithm SHA256
$manifest | Select-Object record_count, first_timestamp, last_timestamp, coverage, remaining

```

Then inspect the last relevant user/assistant records in the raw JSONL. Confirm
that they include the accepted lint revision, final evidence alignment, final
assistant response and your final review. Update coverage/remaining in the
manifest to state exactly what was checked. A timestamp alone does not prove
coverage. If another session contains relevant Assignment 3 work, export its
original records separately under this directory and add a corresponding
manifest entry; do not import unrelated Assignment 2 sessions.

If the manifest's source path is unavailable or the record is not the active
session, export the original session from the client and verify its identity
before replacing anything. Keep final coverage pending until that succeeds.

After refreshing, recheck the snapshot hash and the manifest and review the
path-only assign3/submission_files.txt. The existing snapshot/manifest paths
remain in that list; any additional session files must be added explicitly.
Do not stage unrelated evidence or the four helper deletions. This procedure
does not stage, commit, push, or claim a verified fresh clone.
