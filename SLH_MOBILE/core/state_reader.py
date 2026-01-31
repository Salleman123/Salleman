# core/state_reader.py
"""
State Reader - reads vMix XML and extracts current state
Clean separation: ONLY reads, never writes
"""

from dataclasses import dataclass
from typing import Dict, Optional
import xml.etree.ElementTree as ET


def parse_time_to_seconds(time_str: str) -> Optional[int]:
    """
    Parse time string to seconds.
    Supports: 'MM:SS', 'HH:MM:SS', '20:00', '5:00', etc.
    Returns None if invalid.
    """
    if not time_str:
        return None
    
    s = time_str.strip()
    if not s or s in ("", "0", "00"):
        return 0

    parts = s.split(":")
    try:
        if len(parts) == 2:
            mm = int(parts[0])
            ss = int(parts[1])
            return mm * 60 + ss
        elif len(parts) == 3:
            hh = int(parts[0])
            mm = int(parts[1])
            ss = int(parts[2])
            return hh * 3600 + mm * 60 + ss
    except ValueError:
        return None
    
    return None


def format_seconds_to_mmss(seconds: int) -> str:
    """Format seconds to MM:SS"""
    if seconds < 0:
        seconds = 0
    mm = seconds // 60
    ss = seconds % 60
    return f"{mm:02d}:{ss:02d}"


@dataclass
class PenaltyState:
    """State for one penalty slot"""
    slot: str
    time_raw: str
    seconds: Optional[int]
    active: bool
    number: str


@dataclass
class GameState:
    """Complete game state from vMix XML"""
    # Clock
    clock_raw: str
    clock_seconds: Optional[int]
    
    # Scores
    home_score: str
    away_score: str
    
    # Period
    period: str
    
    # Penalties
    penalties: Dict[str, PenaltyState]
    
    # Scoreboard overlay status
    scoreboard_visible: bool


class StateReader:
    """
    Reads vMix XML and extracts game state.
    ONLY reads - never writes to vMix.
    """

    def __init__(self, vmix_client, config: dict):
        self.client = vmix_client
        self.config = config
        self.sb_cfg = config.get("scoreboard", {})
        self.sb_input = self.sb_cfg.get("input", "")

    def _get_scoreboard_input_number(self) -> str:
        """Get scoreboard input number"""
        num = self.client.find_input_number(self.sb_input)
        if num is None:
            raise RuntimeError(f"Scoreboard input not found: {self.sb_input}")
        return num

    def _extract_text_fields(self, root: ET.Element) -> Dict[str, str]:
        """
        Extract all text fields from scoreboard input.
        Returns dict: {field_name: value}
        """
        sb_num = self._get_scoreboard_input_number()
        
        texts = {}
        for inp in root.findall("./inputs/input"):
            if inp.get("number") == sb_num:
                for txt in inp.findall("./text"):
                    name = txt.get("name") or ""
                    value = (txt.text or "").strip()
                    texts[name] = value
                break
        
        return texts

    def _check_scoreboard_overlay(self, root: ET.Element) -> bool:
        """
        Check if scoreboard is visible on overlay channel.
        Reads <overlays><overlay number="X">INPUTNUM</overlay></overlays>
        """
        sb_num = self._get_scoreboard_input_number()
        channel = int(self.sb_cfg.get("overlay_channel", 1))

        overlays_node = root.find("./overlays")
        if overlays_node is None:
            return False

        for ov in overlays_node.findall("overlay"):
            num_attr = ov.get("number")
            if num_attr != str(channel):
                continue
            text_val = (ov.text or "").strip()
            if text_val == sb_num:
                return True
        
        return False

    def read_state(self) -> GameState:
        """
        Read complete game state from vMix XML.
        This is the ONLY source of truth.
        
        NOTE: Does NOT auto-clear penalties - that's handled by main_window.
        """
        root = self.client.get_status_xml()
        texts = self._extract_text_fields(root)

        # Clock
        clock_field = self.sb_cfg.get("clock_field", "Time.Text")
        clock_raw = texts.get(clock_field, "00:00")
        clock_seconds = parse_time_to_seconds(clock_raw)

        # Scores
        home_score = texts.get(self.sb_cfg.get("home_score_field", ""), "0")
        away_score = texts.get(self.sb_cfg.get("away_score_field", ""), "0")

        # Period
        period = texts.get(self.sb_cfg.get("period_field", ""), "1")

        # Penalties
        penalties = {}
        pen_cfg = self.sb_cfg.get("penalties", {})
        
        for slot, fields in pen_cfg.items():
            time_field = fields.get("time_field", "")
            number_field = fields.get("number_field", "")
            
            time_raw = texts.get(time_field, "00:00")
            seconds = parse_time_to_seconds(time_raw)
            active = seconds is not None and seconds > 0
            number = texts.get(number_field, "")

            penalties[slot] = PenaltyState(
                slot=slot,
                time_raw=time_raw,
                seconds=seconds,
                active=active,
                number=number
            )

        # Scoreboard overlay
        scoreboard_visible = self._check_scoreboard_overlay(root)

        return GameState(
            clock_raw=clock_raw,
            clock_seconds=clock_seconds,
            home_score=home_score,
            away_score=away_score,
            period=period,
            penalties=penalties,
            scoreboard_visible=scoreboard_visible
        )