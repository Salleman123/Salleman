# core/state_machine.py
"""
State Machine for detecting RUNNING/PAUSED state
by comparing seconds over time.

Follows spec 6.1: "vMix XML is the ONLY truth"
"""

from dataclasses import dataclass
from enum import Enum
from typing import Optional, Dict


class RunState(Enum):
    UNKNOWN = "UNKNOWN"
    RUNNING = "RUNNING"
    PAUSED = "PAUSED"


@dataclass
class Track:
    """Tracks state for one timer (clock or penalty)"""
    state: RunState = RunState.UNKNOWN
    last_seconds: Optional[int] = None
    last_change_time: float = 0.0  # Timestamp of last actual change
    # Simple debounce: requires hits before state change
    candidate: Optional[RunState] = None
    candidate_hits: int = 0


class StateMachine:
    """
    Detects RUNNING/PAUSED by comparing seconds over time:
      - if value decreases => RUNNING
      - if value stays same => PAUSED
      - if value increases (manual reset) => PAUSED (update baseline)
    
    Debounce prevents "fluttering" on state changes.
    """

    def __init__(self):
        self.clock = Track()
        self.penalties: Dict[str, Track] = {}

    def _observe(self, tr: Track, seconds: int) -> RunState:
        """
        Compare current seconds with previous to determine state.
        """
        if tr.last_seconds is None:
            tr.last_seconds = seconds
            return RunState.UNKNOWN

        prev = tr.last_seconds
        tr.last_seconds = seconds

        if seconds < prev:
            # Timer decreased = RUNNING
            return RunState.RUNNING
        else:
            # seconds == prev or seconds > prev = PAUSED
            return RunState.PAUSED

    def _debounce(self, tr: Track, observed: RunState) -> RunState:
        """
        Debounce state changes to prevent fluttering.
        
        Rules:
        - UNKNOWN â†’ anything: immediate
        - PAUSED â†’ RUNNING: immediate (1 hit)
        - RUNNING â†’ PAUSED: requires 5 consecutive hits to prevent vMix timing flutter
        """
        import time
        
        if tr.state == RunState.UNKNOWN:
            # First "real" state: accept immediately
            tr.state = observed
            tr.last_change_time = time.time()
            return tr.state

        if observed == tr.state:
            # Same as current state, reset candidate
            tr.candidate = None
            tr.candidate_hits = 0
            return tr.state

        # Special case: PAUSED â†’ RUNNING (instant response for user click)
        if tr.state == RunState.PAUSED and observed == RunState.RUNNING:
            tr.state = RunState.RUNNING
            tr.candidate = None
            tr.candidate_hits = 0
            tr.last_change_time = time.time()
            return tr.state

        # RUNNING â†’ PAUSED: require 5 consecutive hits
        # This prevents flutter from vMix's internal timing updates
        required_hits = 5 if (tr.state == RunState.RUNNING and observed == RunState.PAUSED) else 2
        
        if tr.candidate != observed:
            tr.candidate = observed
            tr.candidate_hits = 1
        else:
            tr.candidate_hits += 1
            if tr.candidate_hits >= required_hits:
                tr.state = observed
                tr.candidate = None
                tr.candidate_hits = 0
                tr.last_change_time = time.time()

        return tr.state

    # ========================================
    # Public API
    # ========================================
    def update_clock(self, clock_seconds: int) -> RunState:
        """
        Update match clock state with current seconds.
        Returns detected state.
        """
        observed = self._observe(self.clock, clock_seconds)
        return self._debounce(self.clock, observed)

    def update_penalty(self, slot: str, penalty_seconds: int) -> RunState:
        """
        Update penalty slot state with current seconds.
        Returns detected state.
        """
        tr = self.penalties.get(slot)
        if tr is None:
            tr = Track()
            self.penalties[slot] = tr
        observed = self._observe(tr, penalty_seconds)
        return self._debounce(tr, observed)

    def get_clock_state(self) -> RunState:
        """Get current clock state"""
        return self.clock.state

    def get_penalty_state(self, slot: str) -> RunState:
        """Get current penalty state"""
        tr = self.penalties.get(slot)
        return tr.state if tr else RunState.UNKNOWN

    def reset(self):
        """Reset all state (useful when reconnecting to vMix)"""
        self.clock = Track()
        self.penalties.clear()