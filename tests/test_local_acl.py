from pathlib import Path

import pytest

from chaser_agent.local_acl import (
    InsecureRuntimePath, _allowed_windows_sddl, assert_private_runtime_path,
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
