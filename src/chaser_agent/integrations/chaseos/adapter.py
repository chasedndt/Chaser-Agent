"""Convert proposals to ChaseOS-shaped packets without dispatching work."""

from __future__ import annotations

from collections.abc import Mapping
from typing import Any


class ChaseOSProposalAdapter:
    active = False
    adapter_id = "chaseos_proposal_adapter"

    def proposal_packet(self, proposal_type: str, payload: Mapping[str, Any]) -> dict[str, Any]:
        return {
            "adapter_id": self.adapter_id,
            "adapter_status": "inactive",
            "proposal_type": proposal_type,
            "payload": dict(payload),
            "dispatch_status": "not_dispatched",
            "gate_consumption": "future_chaseos_control_plane_boundary",
            "authority": {
                "execute": False,
                "promote_memory": False,
                "mutate_canonical_state": False,
                "call_provider": False,
                "call_external_tool": False,
            },
        }

    def dispatch(self, packet: Mapping[str, Any]) -> None:
        raise RuntimeError("ChaseOS proposal dispatch is inactive in P0.1")
