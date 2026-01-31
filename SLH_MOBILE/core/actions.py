# core/actions.py
"""
VMix Actions - high-level commands to vMix
Follows spec: all actions based on XML state, not internal flags
"""

import threading
import time
from typing import Optional

from .state_reader import parse_time_to_seconds, format_seconds_to_mmss


class VMixActions:
    """
    High-level actions for vMix.
    All commands are stateless - they read current state from XML
    and send appropriate commands.
    """

    def __init__(self, vmix_client, config: dict):
        self.client = vmix_client
        self.config = config
        self.sb_cfg = config.get("scoreboard", {})
        self.sb_input = self.sb_cfg.get("input", "")

    def _get_scoreboard_number(self) -> str:
        """Get scoreboard input number"""
        num = self.client.find_input_number(self.sb_input)
        if num is None:
            raise RuntimeError(f"Scoreboard input not found: {self.sb_input}")
        return num

    # ========================================
    # Clock Control
    # ========================================
    def start_clock(self) -> None:
        """
        Start match clock countdown.
        """
        sb_num = self._get_scoreboard_number()
        clock_field = self.sb_cfg.get("clock_field", "Time.Text")
        
        self.client.call_function(
            "StartCountdown",
            Input=sb_num,
            SelectedName=clock_field
        )

    def pause_clock(self) -> None:
        """
        Pause match clock countdown.
        """
        sb_num = self._get_scoreboard_number()
        clock_field = self.sb_cfg.get("clock_field", "Time.Text")
        
        self.client.call_function(
            "PauseCountdown",
            Input=sb_num,
            SelectedName=clock_field
        )

    def stop_clock(self) -> None:
        """
        Stop match clock completely (resets to start value).
        Used when starting new period.
        """
        sb_num = self._get_scoreboard_number()
        clock_field = self.sb_cfg.get("clock_field", "Time.Text")
        
        self.client.call_function(
            "StopCountdown",
            Input=sb_num,
            SelectedName=clock_field
        )

    def set_clock_time(self, time_str: str) -> None:
        """
        Set clock to specific time (MM:SS).
        Stops countdown first, then sets new value.
        """
        seconds = parse_time_to_seconds(time_str)
        if seconds is None or seconds < 0:
            raise ValueError(f"Invalid time: {time_str}")
        
        formatted = format_seconds_to_mmss(seconds)
        sb_num = self._get_scoreboard_number()
        clock_field = self.sb_cfg.get("clock_field", "Time.Text")

        # Stop, set countdown value, then set text
        self.client.call_function(
            "StopCountdown",
            Input=sb_num,
            SelectedName=clock_field
        )
        self.client.call_function(
            "SetCountdown",
            Input=sb_num,
            SelectedName=clock_field,
            Value=formatted
        )
        self.client.set_text(sb_num, clock_field, formatted)

    def adjust_clock(self, delta_seconds: int) -> None:
        """
        Adjust clock by Â±seconds.
        """
        if delta_seconds == 0:
            return
        
        sb_num = self._get_scoreboard_number()
        clock_field = self.sb_cfg.get("clock_field", "Time.Text")
        
        self.client.call_function(
            "AdjustCountdown",
            Input=sb_num,
            SelectedName=clock_field,
            Value=str(delta_seconds)
        )

    # ========================================
    # Penalty Control
    # ========================================
    def start_penalty(self, slot: str) -> None:
        """Start penalty countdown"""
        fields = self._get_penalty_fields(slot)
        time_field = fields.get("time_field")
        if not time_field:
            return
        
        sb_num = self._get_scoreboard_number()
        self.client.call_function(
            "StartCountdown",
            Input=sb_num,
            SelectedName=time_field
        )

    def pause_penalty(self, slot: str) -> None:
        """Pause penalty countdown"""
        fields = self._get_penalty_fields(slot)
        time_field = fields.get("time_field")
        if not time_field:
            return
        
        sb_num = self._get_scoreboard_number()
        self.client.call_function(
            "PauseCountdown",
            Input=sb_num,
            SelectedName=time_field
        )

    def set_penalty(self, slot: str, number: str, time_str: str) -> None:
        """
        Set penalty: stop, set time, set number, make visible.
        Does NOT start countdown - that happens when clock starts.
        """
        seconds = parse_time_to_seconds(time_str)
        if seconds is None or seconds < 0:
            raise ValueError(f"Invalid penalty time: {time_str}")
        
        formatted = format_seconds_to_mmss(seconds)
        fields = self._get_penalty_fields(slot)
        
        time_field = fields.get("time_field")
        number_field = fields.get("number_field")
        time_bg = fields.get("time_bg_field")
        number_bg = fields.get("number_bg_field")
        
        if not time_field or not number_field:
            raise ValueError(f"Missing fields for penalty {slot}")
        
        sb_num = self._get_scoreboard_number()

        # Stop and set time
        self.client.call_function("StopCountdown", Input=sb_num, SelectedName=time_field)
        self.client.call_function("SetCountdown", Input=sb_num, SelectedName=time_field, Value=formatted)
        self.client.set_text(sb_num, time_field, formatted)

        # Set number
        self.client.set_text(sb_num, number_field, number or "")

        # Make visible
        self.client.set_text_visible(sb_num, time_field, True)
        self.client.set_text_visible(sb_num, number_field, True)
        
        if time_bg:
            self.client.set_image_visible(sb_num, time_bg, True)
        if number_bg:
            self.client.set_image_visible(sb_num, number_bg, True)

    def clear_penalty(self, slot: str) -> None:
        """
        Clear penalty: stop, reset to 00:00, hide all fields.
        """
        fields = self._get_penalty_fields(slot)
        time_field = fields.get("time_field")
        number_field = fields.get("number_field")
        time_bg = fields.get("time_bg_field")
        number_bg = fields.get("number_bg_field")
        
        if not time_field or not number_field:
            return
        
        sb_num = self._get_scoreboard_number()

        # Stop countdown
        self.client.call_function("StopCountdown", Input=sb_num, SelectedName=time_field)
        
        # Hide visibility FIRST (so user doesn't see "00:00")
        self.client.set_text_visible(sb_num, time_field, False)
        self.client.set_text_visible(sb_num, number_field, False)
        
        if time_bg:
            self.client.set_image_visible(sb_num, time_bg, False)
        if number_bg:
            self.client.set_image_visible(sb_num, number_bg, False)
        
        # Clear text values (now hidden)
        self.client.set_text(sb_num, time_field, "")
        self.client.set_text(sb_num, number_field, "")
        
        # Reset countdown value
        self.client.call_function("SetCountdown", Input=sb_num, SelectedName=time_field, Value="00:00")

    def adjust_penalty(self, slot: str, delta_seconds: int) -> None:
        """Adjust penalty time by Â±seconds"""
        if delta_seconds == 0:
            return
        
        fields = self._get_penalty_fields(slot)
        time_field = fields.get("time_field")
        if not time_field:
            return
        
        sb_num = self._get_scoreboard_number()
        self.client.call_function(
            "AdjustCountdown",
            Input=sb_num,
            SelectedName=time_field,
            Value=str(delta_seconds)
        )

    def _get_penalty_fields(self, slot: str) -> dict:
        """Get field names for penalty slot"""
        pen_cfg = self.sb_cfg.get("penalties", {})
        return pen_cfg.get(slot.upper(), {})

    # ========================================
    # Score Control
    # ========================================
    def increment_score(self, side: str, delta: int = 1) -> int:
        """
        Increment/decrement score.
        Returns new score value.
        """
        field = (
            self.sb_cfg.get("home_score_field")
            if side.lower() == "home"
            else self.sb_cfg.get("away_score_field")
        )
        if not field:
            return 0
        
        sb_num = self._get_scoreboard_number()
        current = self.client.get_text_field(sb_num, field)
        
        try:
            score = int(current)
        except (ValueError, TypeError):
            score = 0
        
        new_score = max(0, score + delta)
        self.client.set_text(sb_num, field, str(new_score))
        return new_score

    # ========================================
    # Period Control
    # ========================================
    def set_period(self, period: str) -> None:
        """Set period number"""
        field = self.sb_cfg.get("period_field")
        if not field:
            return
        
        sb_num = self._get_scoreboard_number()
        self.client.set_text(sb_num, field, period)

    # ========================================
    # Scoreboard Overlay
    # ========================================
    def show_scoreboard(self) -> None:
        """Show scoreboard overlay"""
        sb_num = self._get_scoreboard_number()
        channel = int(self.sb_cfg.get("overlay_channel", 1))
        self.client.overlay_on(sb_num, channel)

    def hide_scoreboard(self) -> None:
        """Hide scoreboard overlay"""
        sb_num = self._get_scoreboard_number()
        channel = int(self.sb_cfg.get("overlay_channel", 1))
        self.client.overlay_off(sb_num, channel)

    # ========================================
    # Empty Goal
    # ========================================
    def set_empty_goal(self, side: str, visible: bool) -> None:
        """Toggle empty goal visibility"""
        if side.lower() == "home":
            text_field = self.sb_cfg.get("home_empty_field")
            bg_field = self.sb_cfg.get("home_empty_bg_field")
        else:
            text_field = self.sb_cfg.get("away_empty_field")
            bg_field = self.sb_cfg.get("away_empty_bg_field")
        
        if not text_field:
            return
        
        sb_num = self._get_scoreboard_number()
        self.client.set_text_visible(sb_num, text_field, visible)
        
        if bg_field:
            self.client.set_image_visible(sb_num, bg_field, visible)

    # ========================================
    # Goal Graphics
    # ========================================
    def trigger_goal_graphic(self, logger=None) -> None:
        """
        Show GOAL graphic (MÃ…Ã…Ã…L MÃ…Ã…Ã…L MÃ…Ã…Ã…L) with duration.
        Runs in background thread.
        """
        goal_cfg = self.config.get("goal_graphic", {})
        goal_input = goal_cfg.get("input")
        
        if logger:
            logger(f"Goal graphic: input={goal_input}")
        
        if not goal_input:
            if logger:
                logger("Goal graphic: NO INPUT CONFIGURED")
            return
        
        channel = int(goal_cfg.get("overlay_channel", 2))
        duration_ms = int(goal_cfg.get("duration_ms", 5000))
        
        if logger:
            logger(f"Goal graphic: channel={channel}, duration={duration_ms}ms")

        def worker():
            try:
                if logger:
                    logger(f"Goal graphic: Showing on overlay {channel}")
                self.client.overlay_on(goal_input, channel)
                time.sleep(duration_ms / 1000.0)
                self.client.overlay_off(goal_input, channel)
                if logger:
                    logger(f"Goal graphic: Hidden")
            except Exception as e:
                if logger:
                    logger(f"Goal graphic ERROR: {e}")

        threading.Thread(target=worker, daemon=True).start()

    def trigger_after_goal_graphic(self, player_number: str, player_name: str, team: str, wait_after_goal_ms: int = 0, logger=None) -> None:
        """
        Show After Goal graphic with player info.
        Waits for GOAL graphic to finish first (based on wait_after_goal_ms).
        Runs in background thread.
        
        Args:
            player_number: Player jersey number
            player_name: Player name
            team: Team name (HOME/AWAY)
            wait_after_goal_ms: How long to wait AFTER goal graphic finishes before showing this
            logger: Optional logger function
        """
        after_cfg = self.config.get("after_goal_graphic", {})
        after_input = after_cfg.get("input")
        
        if logger:
            logger(f"After goal graphic: input={after_input}")
        
        if not after_input:
            if logger:
                logger("After goal graphic: NO INPUT CONFIGURED")
            return
        
        channel = int(after_cfg.get("overlay_channel", 2))
        duration_ms = int(after_cfg.get("duration_ms", 4000))
        
        # Field mappings
        name_field = after_cfg.get("name_field", "Name.Text")
        number_field = after_cfg.get("number_field", "ShirtNr.Text")
        team_field = after_cfg.get("team_field", "Team.Text")
        
        if logger:
            logger(f"After goal: waiting {wait_after_goal_ms}ms, then showing for {duration_ms}ms on channel {channel}")

        def worker():
            try:
                # Wait for goal graphic to finish + extra delay
                time.sleep(wait_after_goal_ms / 1000.0)
                
                # Find input number
                inp_num = self.client.find_input_number(after_input)
                if not inp_num:
                    if logger:
                        logger(f"After goal ERROR: Input not found: {after_input}")
                    return
                
                # Set fields
                if logger:
                    logger(f"After goal: Setting fields - #{player_number} {player_name} ({team})")
                
                self.client.set_text(inp_num, name_field, player_name)
                self.client.set_text(inp_num, number_field, player_number)
                self.client.set_text(inp_num, team_field, team)
                
                # Show overlay
                if logger:
                    logger(f"After goal: Showing on overlay {channel}")
                self.client.overlay_on(after_input, channel)
                
                time.sleep(duration_ms / 1000.0)
                
                # Hide overlay
                self.client.overlay_off(after_input, channel)
                if logger:
                    logger(f"After goal: Hidden")
                    
            except Exception as e:
                if logger:
                    logger(f"After goal ERROR: {e}")

        threading.Thread(target=worker, daemon=True).start()
    # ========================================
    # Nameplate Control
    # ========================================
    
    def show_nameplate(self, person_type: str, player_number: str, player_name: str, team: str, logger=None):
        """
        Show nameplate overlay.
        
        Args:
            person_type: "player" or "staff" - determines which input to use
            player_number: Player jersey number (empty for staff)
            player_name: Person name
            team: Team identifier ("home", "away", or "general")
            logger: Optional logging function
        """
        np_cfg = self.config.get("nameplate", {})
        
        # Choose correct input based on person type
        if person_type == "player":
            np_input = np_cfg.get("player_input", "NAMNSKYLT MED Nr")
        else:  # staff
            np_input = np_cfg.get("staff_input", "NAMNSKYLT TRÄNARE")
        
        channel = np_cfg.get("overlay_channel", 3)
        name_field = np_cfg.get("name_field", "Name.Text")
        number_field = np_cfg.get("number_field", "ShirtNr.Text")
        team_field = np_cfg.get("team_field", "Team.Text")
        logo_field = np_cfg.get("logo_field", "Logo.Source")
        
        try:
            # Find input number
            inp_num = self.client.find_input_number(np_input)
            if not inp_num:
                raise RuntimeError(f"Nameplate input not found: {np_input}")
            
            # Determine team name and logo path FROM SCOREBOARD
            sb_num = self._get_scoreboard_number()
            root = self.client.get_status_xml()
            
            team_name = ""
            logo_path = ""
            
            # Find scoreboard input
            for inp in root.findall("./inputs/input"):
                if inp.get("number") == sb_num:
                    if team == "home":
                        # Get home team name
                        for txt in inp.findall("./text"):
                            if txt.get("name") == self.sb_cfg.get("home_name_field"):
                                team_name = (txt.text or "").strip()
                                break
                        
                        # Get home logo from scoreboard
                        home_logo_field = self.sb_cfg.get("home_logo_field", "HomeLogo.Source")
                        for img in inp.findall("./image"):
                            if img.get("name") == home_logo_field:
                                logo_path = (img.text or "").strip()
                                break
                                
                    elif team == "away":
                        # Get away team name
                        for txt in inp.findall("./text"):
                            if txt.get("name") == self.sb_cfg.get("away_name_field"):
                                team_name = (txt.text or "").strip()
                                break
                        
                        # Get away logo from scoreboard
                        away_logo_field = self.sb_cfg.get("away_logo_field", "AwayLogo.Source")
                        for img in inp.findall("./image"):
                            if img.get("name") == away_logo_field:
                                logo_path = (img.text or "").strip()
                                break
                    break
            
            # Set fields
            if logger:
                type_label = "Spelare" if person_type == "player" else "Ledare"
                if player_number:
                    logger(f"Nameplate: {type_label} #{player_number} {player_name} ({team})")
                else:
                    logger(f"Nameplate: {type_label} {player_name} ({team})")
            
            self.client.set_text(inp_num, name_field, player_name)
            
            # Only set number for players
            if person_type == "player":
                self.client.set_text(inp_num, number_field, player_number)
            
            self.client.set_text(inp_num, team_field, team_name)
            
            if logo_path:
                self.client.set_text(inp_num, logo_field, logo_path)
            
            # Show overlay
            if logger:
                logger(f"Nameplate: Showing '{np_input}' on overlay {channel}")
            self.client.overlay_on(np_input, channel)
            
            # Store current input for hide_nameplate
            self._current_nameplate_input = np_input
            
        except Exception as e:
            if logger:
                logger(f"Nameplate ERROR: {e}")
            raise
    
    def hide_nameplate(self, logger=None):
        """
        Hide nameplate overlay.
        
        Args:
            logger: Optional logging function
        """
        np_cfg = self.config.get("nameplate", {})
        channel = np_cfg.get("overlay_channel", 3)
        
        # Use stored input name if available, otherwise try both
        np_input = getattr(self, '_current_nameplate_input', None)
        
        if np_input:
            inputs_to_hide = [np_input]
        else:
            # If we don't know which is showing, hide both
            inputs_to_hide = [
                np_cfg.get("player_input", "NAMNSKYLT MED Nr"),
                np_cfg.get("staff_input", "NAMNSKYLT TRÄNARE")
            ]
        
        try:
            for inp in inputs_to_hide:
                try:
                    self.client.overlay_off(inp, channel)
                except:
                    pass  # Ignore if input doesn't exist
            
            if logger:
                logger(f"Nameplate: Hidden")

                
        except Exception as e:
            if logger:
                logger(f"Nameplate hide ERROR: {e}")
            raise
