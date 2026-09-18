"""FREE self-service product policy. Server-owned; never customer supplied."""
from dataclasses import dataclass

@dataclass(frozen=True)
class FreePolicy:
    adapter_slots: tuple[str, ...] = ("primary",)
    require_all_adapters: bool = True
    primary_tuning: str = "12"
    max_authorized_websites: int = 1

POLICY = FreePolicy()
