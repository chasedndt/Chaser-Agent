from dataclasses import dataclass

@dataclass(frozen=True)
class ChaserAgentConfig:
    env: str = "local"
    allow_external_calls: bool = False
    allow_canonical_writeback: bool = False
