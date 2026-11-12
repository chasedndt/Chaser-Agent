import os
from pathlib import Path

import pytest

from chaser_agent.local_acl import (
    InsecureRuntimePath, _allowed_windows_sddl, assert_private_runtime_path, read_private_control_token,
)

SID = "S-1-5-21-100-200-300-1001"


def test_private_windows_acl_requires_current_user_and_no_broad_grants():
    private = f"O:{SID}G:{SID}D:P(A;;FA;;;{SID})(A;;FA;;;SY)(A;;FA;;;BA)"
    assert _allowed_windows_sddl(private, SID)
    assert not _allowed_windows_sddl(private + "(A;;GR;;;BU)", SID)
    assert not _allowed_windows_sddl(private + "(A;;GW;;;AU)", SID)
    assert not _allowed_windows_sddl(private.replace(f"O:{SID}", "O:S-1-5-21-999-999-999-999"), SID)
    assert not _allowed_windows_sddl(private.replace(f"(A;;FA;;;{SID})", ""), SID)


def test_actual_inherited_runtime_acl_is_refused_without_changing_it():
    # A pure parser assertion over the read-only SDDL captured from this E:
    # runtime; no ACL writes, user identity assumptions or token reads occur.
    broad = (
        f"O:{SID}G:{SID}D:(A;ID;FA;;;BA)(A;ID;FA;;;SY)"
        "(A;ID;0x1301bf;;;AU)(A;ID;0x1200a9;;;BU)"
    )
    assert not _allowed_windows_sddl(broad, SID)


def test_acl_parser_rejects_unparsed_dacl_text_and_unknown_ace_types():
    private = f"O:{SID}G:{SID}D:PAI(A;;FA;;;{SID})(A;;FA;;;SY)"
    assert _allowed_windows_sddl(private, SID)
    assert not _allowed_windows_sddl(private + "A", SID)
    assert not _allowed_windows_sddl(private.replace("(A;;FA;;;SY)", "(XA;;FA;;;SY)"), SID)


def test_missing_runtime_path_fails_closed(tmp_path: Path):
    with pytest.raises(InsecureRuntimePath):
        assert_private_runtime_path(tmp_path / "missing")


def test_client_checks_directory_and_token_before_read(tmp_path: Path, monkeypatch):
    token_path = tmp_path / "control-token"
    token_path.write_text("a" * 64, encoding="ascii")
    checked = []

    def private(path: Path):
        checked.append(path)

    monkeypatch.setattr("chaser_agent.local_acl.assert_private_runtime_path", private)
    assert read_private_control_token(tmp_path) == "a" * 64
    assert checked == [tmp_path, token_path]
    token_path.write_text("not a token", encoding="ascii")
    with pytest.raises(InsecureRuntimePath, match="invalid"):
        read_private_control_token(tmp_path)


def test_client_never_reads_token_when_directory_is_broad(tmp_path: Path, monkeypatch):
    (tmp_path / "control-token").write_text("a" * 64, encoding="ascii")

    def broad(path: Path):
        if path == tmp_path:
            raise InsecureRuntimePath("broad ACL")

    monkeypatch.setattr("chaser_agent.local_acl.assert_private_runtime_path", broad)
    with pytest.raises(InsecureRuntimePath, match="broad ACL"):
        read_private_control_token(tmp_path)


def test_owner_rights_count_only_when_the_user_owns_the_path() -> None:
    user = "S-1-5-21-1-2-3-1005"
    other = "S-1-5-21-9-9-9-1006"
    aces = "D:P(A;OICI;FA;;;OW)(A;OICI;FA;;;SY)(A;OICI;FA;;;BA)"
    assert _allowed_windows_sddl(f"O:{user}G:{user}{aces}", user) is True
    assert _allowed_windows_sddl(f"O:BAG:BA{aces}", user) is False
    assert _allowed_windows_sddl(f"O:{other}G:{other}{aces}", user) is False


@pytest.mark.skipif(os.name != "nt", reason="Windows security descriptors")
def test_the_api_reader_matches_what_windows_reports_for_a_real_path(tmp_path: Path) -> None:
    import subprocess

    from chaser_agent.local_acl import _windows_acl

    script = "$ErrorActionPreference='Stop'; [System.Security.Principal.WindowsIdentity]::GetCurrent().User.Value; (Get-Acl -LiteralPath $env:CHASER_ACL_TARGET).Sddl"
    done = subprocess.run(["powershell.exe", "-NoProfile", "-NonInteractive", "-Command", script], env={**os.environ, "CHASER_ACL_TARGET": str(tmp_path)}, capture_output=True, text=True, timeout=60, check=True)
    expected_sid, expected_sddl = [line.strip() for line in done.stdout.strip().splitlines()]
    sid, sddl = _windows_acl(tmp_path)

    def parts(text: str) -> tuple[str, list[str]]:
        # PowerShell sorts the entries and the API returns them as stored. The gate treats them as a set.
        return text[: text.index("(")], sorted(text[text.index("(") + 1 : -1].split(")("))

    assert sid == expected_sid
    assert parts(sddl) == parts(expected_sddl)


@pytest.mark.skipif(os.name != "nt", reason="Windows security descriptors")
def test_a_missing_path_fails_closed(tmp_path: Path) -> None:
    from chaser_agent.local_acl import _windows_acl

    with pytest.raises(InsecureRuntimePath):
        _windows_acl(tmp_path / "missing")
