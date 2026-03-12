"""
Resource Manager
────────────────
Simulates cloud container allocation.
Maintains an internal count of running containers
and exposes scale_up / scale_down / set operations.
"""


class ResourceManager:
    """Simulated cloud resource pool."""

    def __init__(self, initial_containers: int = 3):
        self._containers = max(1, initial_containers)
        self._history: list[dict] = []     # audit trail

    # ── queries ──────────────────────────────
    def get_current_resources(self) -> dict:
        """Return current resource state."""
        return {
            "containers": self._containers,
            "capacity": self._containers * 100,   # 100 reqs/container
        }

    def get_history(self) -> list[dict]:
        """Return the full scaling history."""
        return list(self._history)

    # ── mutations ────────────────────────────
    def scale_up(self, n: int = 1) -> dict:
        """Add *n* containers."""
        old = self._containers
        self._containers += n
        self._log("scale_up", old, self._containers)
        return self.get_current_resources()

    def scale_down(self, n: int = 1) -> dict:
        """Remove *n* containers (minimum 1 always kept)."""
        old = self._containers
        self._containers = max(1, self._containers - n)
        self._log("scale_down", old, self._containers)
        return self.get_current_resources()

    def set_containers(self, target: int) -> dict:
        """Directly set the container count to *target*."""
        old = self._containers
        self._containers = max(1, target)
        action = "scale_up" if self._containers > old else (
            "scale_down" if self._containers < old else "no_change"
        )
        self._log(action, old, self._containers)
        return self.get_current_resources()

    # ── internals ────────────────────────────
    def _log(self, action: str, old: int, new: int):
        self._history.append({
            "action": action,
            "from": old,
            "to": new,
        })

    def __repr__(self):
        return f"ResourceManager(containers={self._containers})"
