# gui/main_window_mobile.py
"""
Main Window for SLH - MOBILE OPTIMIZED LAYOUT
Kompakt design för enhandsanvändning på mobil
"""

import tkinter as tk
from tkinter import scrolledtext, messagebox
from datetime import datetime
import sys

from core import VMixClient, StateReader, StateMachine, VMixActions, RunState, DataSourceManager
from core.lineup_state import LineupState
from core.export_engine import ExportEngine
from core.json_exporter import JSONExporter
from gui.dialogs import PeriodEndDialog, GoalScorerDialog, PenaltyDialog, NameplateDialog
from gui.settings_window import SettingsWindow
from gui.startup_dialog import StartupDialog


class MainWindowMobile(tk.Tk):
    """
    Mobilanpassat huvudfönster med kompakt layout.
    
    Layout (uppifrån och ner):
    1. Top bar: INSTÄLLNINGAR | ÅTERANSLUT
    2. Period buttons: P1 P2 P3 OT
    3. Scoreboard toggle: VISA/DÖLJ SCOREBOARD
    4. Tom målbur: HEMMA | BORTA
    5. Huvudsektion (3 kolumner):
       - Vänster: MÅL HEMMA + score + korrektion
       - Mitten: MATCHKLOCKA (stor) + START/PAUS + justering
       - Höger: MÅL BORTA + score + korrektion
    6. Utvisningar: H1 H2 | A1 A2
    """

    def __init__(self, config: dict):
        super().__init__()
        
        self.config = config
        self.title("SLH - Scoreboard Helper")
        
        # Make window responsive
        self.geometry("600x900")
        self.minsize(400, 700)
        
        # Core components
        self.client = None
        self.state_reader = None
        self.state_machine = None
        self.actions = None
        
        # DataSource Manager
        self.data_manager = DataSourceManager()
        
        # Lineup State (centralized storage)
        self.lineup_state = LineupState()
        
        # Export Engine (will be initialized after vMix connection)
        self.export_engine = None
        
        # JSON Exporter (initialized after lineup load)
        self.json_exporter = None
        
        # State
        self.last_game_state = None
        self.last_penalty_seconds = {}
        self.period_end_shown = False
        self.polling_active = False
        self.poll_interval = config.get("polling", {}).get("interval_ms", 200)
        
        # Empty goal state
        self.home_empty_active = False
        self.away_empty_active = False
        
        # Nameplate state
        self.nameplate_visible = False
        
        # Build UI
        self._build_ui()
        
        # Show vMix connection dialog at startup
        self.after(100, self._show_vmix_connection_dialog)

    def _build_ui(self):
        """Build mobile-optimized UI"""
        
        # ===== TOP BAR =====
        top_bar = tk.Frame(self, bg="#2c3e50", height=50)
        top_bar.pack(fill=tk.X)
        top_bar.pack_propagate(False)
        
        # Status indicator
        self.status_label = tk.Label(
            top_bar,
            text="● EJ ANSLUTEN",
            bg="#2c3e50",
            fg="white",
            font=("Segoe UI", 11, "bold")
        )
        self.status_label.pack(side=tk.LEFT, padx=15, pady=10)
        
        # Buttons
        tk.Button(
            top_bar,
            text="ÅTERANSLUT",
            font=("Segoe UI", 9),
            command=self._connect_to_vmix,
            bg="#34495e",
            fg="white",
            relief="flat",
            padx=10
        ).pack(side=tk.RIGHT, padx=5, pady=10)
        
        tk.Button(
            top_bar,
            text="INSTÄLLNINGAR",
            font=("Segoe UI", 9),
            command=self._open_settings,
            bg="#34495e",
            fg="white",
            relief="flat",
            padx=10
        ).pack(side=tk.RIGHT, padx=5, pady=10)
        
        # ===== MAIN CONTENT =====
        main_frame = tk.Frame(self, bg="#ecf0f1")
        main_frame.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        
        # ----- PERIOD BUTTONS -----
        self._build_period_section(main_frame)
        
        # ----- SCOREBOARD TOGGLE -----
        self._build_scoreboard_section(main_frame)
        
        # ----- HUVUDSEKTION: TOM MÅLBUR + MÅL + KLOCKA -----
        self._build_main_section(main_frame)
        
        # ----- UTVISNINGAR -----
        self._build_penalty_section(main_frame)
        
        # ----- LOG (collapse/expand) -----
        self._build_log_section(main_frame)

    def _build_period_section(self, parent):
        """Period selection buttons"""
        frame = tk.Frame(parent, bg="#ecf0f1")
        frame.pack(fill=tk.X, pady=5)
        
        tk.Label(
            frame,
            text="PERIOD:",
            bg="#ecf0f1",
            font=("Segoe UI", 10, "bold")
        ).pack(side=tk.LEFT, padx=10)
        
        # Store button references for highlighting
        self.period_buttons = {}
        
        periods = [("P1", "1"), ("P2", "2"), ("P3", "3"), ("OT", "OT")]
        
        for label, value in periods:
            btn = tk.Button(
                frame,
                text=label,
                width=4,
                height=1,
                font=("Segoe UI", 10, "bold"),
                command=lambda v=value: self._on_period_click(v),
                bg="white",
                relief="raised",
                bd=2
            )
            btn.pack(side=tk.LEFT, padx=3)
            self.period_buttons[value] = btn

    def _build_scoreboard_section(self, parent):
        """Scoreboard and Nameplate toggle buttons side by side"""
        frame = tk.Frame(parent, bg="#ecf0f1")
        frame.pack(fill=tk.X, pady=5)
        
        # Scoreboard button (left)
        self.scoreboard_btn = tk.Button(
            frame,
            text="VISA SCOREBOARD",
            font=("Segoe UI", 11, "bold"),
            height=2,
            command=self._on_scoreboard_toggle,
            bg="#bdc3c7",
            fg="black",
            relief="raised",
            bd=3
        )
        self.scoreboard_btn.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=(10, 5))
        
        # Nameplate button (right)
        self.nameplate_btn = tk.Button(
            frame,
            text="NAMNSKYLT",
            font=("Segoe UI", 11, "bold"),
            height=2,
            command=self._on_nameplate_click,
            bg="#9C27B0",
            fg="white",
            relief="raised",
            bd=3
        )
        self.nameplate_btn.pack(side=tk.RIGHT, fill=tk.X, expand=True, padx=(5, 10))

    def _build_main_section(self, parent):
        """Main section: TOM MÅLBUR + GOAL HOME | CLOCK | GOAL AWAY"""
        frame = tk.Frame(parent, bg="#ecf0f1")
        frame.pack(fill=tk.BOTH, expand=True, pady=5)
        
        # ----- LEFT: MÅL HEMMA -----
        left_frame = tk.Frame(frame, bg="#e8f5e9", relief="solid", bd=2)
        left_frame.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=(10, 5))
        
        # Header: HEMMA
        tk.Label(
            left_frame,
            text="HEMMA",
            font=("Segoe UI", 14, "bold"),
            bg="#e8f5e9",
            fg="#2e7d32"
        ).pack(pady=(5, 5))
        
        # NAMN button (quick access)
        tk.Button(
            left_frame,
            text="NAMN",
            font=("Segoe UI", 9, "bold"),
            height=1,
            command=lambda: self._on_nameplate("home"),
            bg="#7cb342",
            fg="white",
            relief="raised",
            bd=2
        ).pack(fill=tk.X, padx=5, pady=(0, 5))
        
        # TOM MÅLBUR button
        self.empty_home_btn = tk.Button(
            left_frame,
            text="TOM MÅLBUR",
            font=("Segoe UI", 10, "bold"),
            height=2,
            command=lambda: self._on_empty_goal_toggle("home"),
            bg="white",
            relief="raised",
            bd=2
        )
        self.empty_home_btn.pack(fill=tk.X, padx=5, pady=(0, 5))
        
        # Correction buttons (ABOVE MÅL)
        home_corr = tk.Frame(left_frame, bg="#e8f5e9")
        home_corr.pack(pady=(0, 5))
        
        tk.Button(
            home_corr,
            text="-1",
            width=6,
            font=("Segoe UI", 10),
            command=lambda: self._on_score_correction("home", -1),
            bg="white"
        ).pack(side=tk.LEFT, padx=2)
        
        tk.Button(
            home_corr,
            text="+1",
            width=6,
            font=("Segoe UI", 10),
            command=lambda: self._on_score_correction("home", +1),
            bg="white"
        ).pack(side=tk.LEFT, padx=2)
        
        # MÅL button
        self.home_goal_btn = tk.Button(
            left_frame,
            text="MÅL\n0",
            font=("Segoe UI", 24, "bold"),
            height=2,
            command=lambda: self._on_goal("home"),
            bg="#c8e6c9",
            fg="#2e7d32",
            relief="raised",
            bd=3,
            state='disabled'  # Disabled at start (clock is paused)
        )
        self.home_goal_btn.pack(fill=tk.X, padx=5, pady=(0, 5))
        
        # ----- CENTER: MATCHKLOCKA -----
        center_frame = tk.Frame(frame, bg="#fff3e0", relief="solid", bd=2)
        center_frame.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=5)
        
        # Adjustment buttons (ABOVE clock)
        adj_frame = tk.Frame(center_frame, bg="#fff3e0")
        adj_frame.pack(pady=(5, 0))
        
        self.adj_minus5 = tk.Button(
            adj_frame,
            text="-5",
            width=5,
            font=("Segoe UI", 9),
            command=lambda: self._on_clock_adjust(-5),
            bg="white"
        )
        self.adj_minus5.grid(row=0, column=0, padx=2)
        
        self.adj_minus1 = tk.Button(
            adj_frame,
            text="-1",
            width=5,
            font=("Segoe UI", 9),
            command=lambda: self._on_clock_adjust(-1),
            bg="white"
        )
        self.adj_minus1.grid(row=0, column=1, padx=2)
        
        tk.Button(
            adj_frame,
            text="+1",
            width=5,
            font=("Segoe UI", 9),
            command=lambda: self._on_clock_adjust(+1),
            bg="white"
        ).grid(row=0, column=2, padx=2)
        
        tk.Button(
            adj_frame,
            text="+5",
            width=5,
            font=("Segoe UI", 9),
            command=lambda: self._on_clock_adjust(+5),
            bg="white"
        ).grid(row=0, column=3, padx=2)
        
        # Time display
        self.time_display = tk.Label(
            center_frame,
            text="20:00",
            font=("Courier New", 48, "bold"),
            bg="white",
            fg="black",
            relief="sunken",
            bd=3,
            height=2
        )
        self.time_display.pack(pady=5, padx=10, fill=tk.X)
        
        # START/PAUS button - square/prominent
        btn_container = tk.Frame(center_frame, bg="white")
        btn_container.pack(pady=(5, 10))
        
        self.clock_toggle_btn = tk.Button(
            btn_container,
            text="START",
            font=("Segoe UI", 18, "bold"),
            width=12,
            height=3,
            command=self._on_clock_toggle,
            bg="green",
            fg="white",
            relief="raised",
            bd=4
        )
        self.clock_toggle_btn.pack(padx=10)
        
        # ----- RIGHT: MÅL BORTA -----
        right_frame = tk.Frame(frame, bg="#ffebee", relief="solid", bd=2)
        right_frame.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=(5, 10))
        
        # Header: BORTA
        tk.Label(
            right_frame,
            text="BORTA",
            font=("Segoe UI", 14, "bold"),
            bg="#ffebee",
            fg="#c62828"
        ).pack(pady=(5, 5))
        
        # NAMN button (quick access)
        tk.Button(
            right_frame,
            text="NAMN",
            font=("Segoe UI", 9, "bold"),
            height=1,
            command=lambda: self._on_nameplate("away"),
            bg="#e53935",
            fg="white",
            relief="raised",
            bd=2
        ).pack(fill=tk.X, padx=5, pady=(0, 5))
        
        # TOM MÅLBUR button
        self.empty_away_btn = tk.Button(
            right_frame,
            text="TOM MÅLBUR",
            font=("Segoe UI", 10, "bold"),
            height=2,
            command=lambda: self._on_empty_goal_toggle("away"),
            bg="white",
            relief="raised",
            bd=2
        )
        self.empty_away_btn.pack(fill=tk.X, padx=5, pady=(0, 5))
        
        # Correction buttons (ABOVE MÅL)
        away_corr = tk.Frame(right_frame, bg="#ffebee")
        away_corr.pack(pady=(0, 5))
        
        tk.Button(
            away_corr,
            text="-1",
            width=6,
            font=("Segoe UI", 10),
            command=lambda: self._on_score_correction("away", -1),
            bg="white"
        ).pack(side=tk.LEFT, padx=2)
        
        tk.Button(
            away_corr,
            text="+1",
            width=6,
            font=("Segoe UI", 10),
            command=lambda: self._on_score_correction("away", +1),
            bg="white"
        ).pack(side=tk.LEFT, padx=2)
        
        # MÅL button
        self.away_goal_btn = tk.Button(
            right_frame,
            text="MÅL\n0",
            font=("Segoe UI", 24, "bold"),
            height=2,
            command=lambda: self._on_goal("away"),
            bg="#ffcdd2",
            fg="#c62828",
            relief="raised",
            bd=3,
            state='disabled'  # Disabled at start (clock is paused)
        )
        self.away_goal_btn.pack(fill=tk.X, padx=5, pady=(0, 5))

    def _build_penalty_section(self, parent):
        """Penalty buttons"""
        frame = tk.Frame(parent, bg="#ecf0f1")
        frame.pack(fill=tk.X, pady=5)
        
        tk.Label(
            frame,
            text="UTVISNINGAR",
            bg="#ecf0f1",
            font=("Segoe UI", 11, "bold")
        ).pack(pady=5)
        
        # Button container
        btn_frame = tk.Frame(frame, bg="#ecf0f1")
        btn_frame.pack()
        
        # Left side: H1, H2
        left = tk.Frame(btn_frame, bg="#ecf0f1")
        left.pack(side=tk.LEFT, padx=10)
        
        self.h1_btn = tk.Button(
            left,
            text="H1\n00:00\n",
            width=10,
            height=4,
            font=("Segoe UI", 11, "bold"),
            command=lambda: self._on_penalty_click("H1"),
            bg="white",
            relief="raised",
            bd=2
        )
        self.h1_btn.pack(side=tk.LEFT, padx=3)
        
        self.h2_btn = tk.Button(
            left,
            text="H2\n00:00\n",
            width=10,
            height=4,
            font=("Segoe UI", 11, "bold"),
            command=lambda: self._on_penalty_click("H2"),
            bg="white",
            relief="raised",
            bd=2
        )
        self.h2_btn.pack(side=tk.LEFT, padx=3)
        
        # Right side: A1, A2
        right = tk.Frame(btn_frame, bg="#ecf0f1")
        right.pack(side=tk.LEFT, padx=10)
        
        self.a1_btn = tk.Button(
            right,
            text="A1\n00:00\n",
            width=10,
            height=4,
            font=("Segoe UI", 11, "bold"),
            command=lambda: self._on_penalty_click("A1"),
            bg="white",
            relief="raised",
            bd=2
        )
        self.a1_btn.pack(side=tk.LEFT, padx=3)
        
        self.a2_btn = tk.Button(
            right,
            text="A2\n00:00\n",
            width=10,
            height=4,
            font=("Segoe UI", 11, "bold"),
            command=lambda: self._on_penalty_click("A2"),
            bg="white",
            relief="raised",
            bd=2
        )
        self.a2_btn.pack(side=tk.LEFT, padx=3)
        
        # Store button references
        self.penalty_buttons = {
            "H1": self.h1_btn,
            "H2": self.h2_btn,
            "A1": self.a1_btn,
            "A2": self.a2_btn
        }

    def _build_log_section(self, parent):
        """Collapsible log section"""
        frame = tk.Frame(parent, bg="#ecf0f1")
        frame.pack(fill=tk.X, pady=5)
        
        # Toggle button
        self.log_toggle_btn = tk.Button(
            frame,
            text="▼ LOGG",
            font=("Segoe UI", 9),
            command=self._toggle_log,
            bg="#95a5a6",
            fg="white",
            relief="flat"
        )
        self.log_toggle_btn.pack(fill=tk.X, padx=10)
        
        # Log text (initially hidden)
        self.log_frame = tk.Frame(frame, bg="#ecf0f1")
        
        self.log_text = scrolledtext.ScrolledText(
            self.log_frame,
            width=60,
            height=10,
            font=("Courier New", 8),
            state=tk.DISABLED,
            bg="#2c3e50",
            fg="#ecf0f1"
        )
        self.log_text.pack(fill=tk.BOTH, expand=True, padx=10, pady=5)
        
        self.log_visible = False

    def _toggle_log(self):
        """Toggle log visibility"""
        if self.log_visible:
            self.log_frame.pack_forget()
            self.log_toggle_btn.config(text="▼ LOGG")
            self.log_visible = False
        else:
            self.log_frame.pack(fill=tk.BOTH, expand=True)
            self.log_toggle_btn.config(text="▲ DÖLJ LOGG")
            self.log_visible = True

    # ========================================
    # Event Handlers
    # ========================================
    
    def _on_period_click(self, period: str):
        """Handle period button click"""
        if self.actions is None:
            return
        
        try:
            self.actions.set_period(period)
            self.log(f"Period satt till: {period}")
        except Exception as e:
            self.log(f"Error setting period: {e}")

    def _on_scoreboard_toggle(self):
        """Toggle scoreboard visibility"""
        if self.actions is None or self.last_game_state is None:
            return
        
        try:
            if self.last_game_state.scoreboard_visible:
                self.actions.hide_scoreboard()
                self.log("Scoreboard dold")
            else:
                self.actions.show_scoreboard()
                self.log("Scoreboard visad")
        except Exception as e:
            self.log(f"Error toggling scoreboard: {e}")

    def _on_empty_goal_toggle(self, side: str):
        """Toggle empty goal"""
        if self.actions is None:
            return
        
        try:
            if side == "home":
                self.home_empty_active = not self.home_empty_active
                self.actions.set_empty_goal("home", self.home_empty_active)
            else:
                self.away_empty_active = not self.away_empty_active
                self.actions.set_empty_goal("away", self.away_empty_active)
            
            self._update_empty_goal_buttons()
            
        except Exception as e:
            self.log(f"Error toggling empty goal: {e}")

    def _on_clock_toggle(self):
        """Toggle clock START/PAUSE"""
        if self.actions is None:
            return
        
        state = self.state_machine.get_clock_state()
        
        if state == RunState.RUNNING:
            # Pause clock and penalties
            self.actions.pause_clock()
            for slot in ["H1", "H2", "A1", "A2"]:
                if self.last_game_state:
                    penalty = self.last_game_state.penalties.get(slot)
                    if penalty and penalty.active:
                        self.actions.pause_penalty(slot)
            
            # Enable adjustment and penalty buttons when paused (administrative changes)
            for btn in self.penalty_buttons.values():
                btn.config(state='normal')
            
            # Disable MÅL buttons when paused (goals scored during play)
            self.home_goal_btn.config(state='disabled')
            self.away_goal_btn.config(state='disabled')
        else:
            # Start clock
            if self.last_game_state and self.last_game_state.clock_seconds:
                if self.last_game_state.clock_seconds > 0:
                    # Auto-show scoreboard
                    if not self.last_game_state.scoreboard_visible:
                        try:
                            self.actions.show_scoreboard()
                            self.log("Auto-showing scoreboard on START")
                        except Exception as e:
                            self.log(f"Error showing scoreboard: {e}")
                    
                    # Start clock and penalties
                    self.actions.start_clock()
                    for slot in ["H1", "H2", "A1", "A2"]:
                        penalty = self.last_game_state.penalties.get(slot)
                        if penalty and penalty.active:
                            self.actions.start_penalty(slot)
            
            # Enable MÅL buttons when running (goals scored during play)
            self.home_goal_btn.config(state='normal')
            self.away_goal_btn.config(state='normal')
            
            # Disable adjustment and penalty buttons when running
            for btn in self.penalty_buttons.values():
                btn.config(state='disabled')

    def _on_clock_adjust(self, delta: int):
        """Adjust clock by delta seconds"""
        if self.actions is None:
            return
        
        try:
            self.actions.adjust_clock(delta)
            
            # Also adjust active penalties
            if self.last_game_state:
                for slot in ["H1", "H2", "A1", "A2"]:
                    penalty = self.last_game_state.penalties.get(slot)
                    if penalty and penalty.active and penalty.seconds and penalty.seconds > 0:
                        self.actions.adjust_penalty(slot, delta)
        except Exception as e:
            self.log(f"Error adjusting time: {e}")

    def _on_goal(self, side: str):
        """Handle goal button click - show GOAL graphic FIRST, then dialog"""
        if self.actions is None:
            return
        
        try:
            # 1. Increment score IMMEDIATELY
            self.actions.increment_score(side, +1)
            
            # 2. Check if clock is running BEFORE pausing
            clock_state = self.state_machine.get_clock_state()
            clock_was_running = (clock_state == RunState.RUNNING)
            
            # 3. Pause if clock was running
            if clock_was_running:
                self.actions.pause_clock()
                self.log(f"Clock paused for goal")
                
                # Also pause all active penalties
                for slot in ["H1", "H2", "A1", "A2"]:
                    if self.last_game_state:
                        penalty = self.last_game_state.penalties.get(slot)
                        if penalty and penalty.active:
                            self.actions.pause_penalty(slot)
            else:
                self.log(f"Clock already paused - not changing state")
            
            # 4. Trigger GOAL graphic IMMEDIATELY (before dialog!)
            self.log(f"Goal: {side.upper()}")
            self.actions.trigger_goal_graphic(logger=self.log)
            
            # 5. Open dialog (still blocking with wait_window, but graphic already shown)
            dialog = GoalScorerDialog(self, self, side)
            self.wait_window(dialog)
            
            # 6. When dialog closes, trigger after-goal graphic if player selected
            if dialog.result:
                number, name = dialog.result
                if number and name:  # Only if actual player selected (not "Ingen spelare")
                    self.log(f"Goal scorer: #{number} {name}")
                    
                    # Trigger after-goal graphic with player info
                    goal_cfg = self.config.get("goal_graphic", {})
                    after_cfg = self.config.get("after_goal_graphic", {})
                    
                    goal_duration = int(goal_cfg.get("duration_ms", 5000))
                    delay_after = int(after_cfg.get("pause_before_ms", 0))
                    total_wait = goal_duration + delay_after
                    
                    team_name = side.upper()
                    self.actions.trigger_after_goal_graphic(
                        player_number=number,
                        player_name=name,
                        team=team_name,
                        wait_after_goal_ms=total_wait,
                        logger=self.log
                    )
                else:
                    self.log(f"Goal registered without player info (Ingen spelare)")
            else:
                self.log(f"Goal scorer cancelled")
                
        except Exception as e:
            self.log(f"Error registering goal: {e}")

    def _on_score_correction(self, side: str, delta: int):
        """Correct score without celebration"""
        if self.actions is None:
            return
        
        try:
            self.actions.increment_score(side, delta)
            self.log(f"Score correction: {side} {delta:+d}")
        except Exception as e:
            self.log(f"Error correcting score: {e}")

    def _on_penalty_click(self, slot: str):
        """Handle penalty button click"""
        if self.actions is None:
            return
        
        # Check if penalty is active
        if self.last_game_state:
            penalty = self.last_game_state.penalties.get(slot)
            if penalty and penalty.active:
                # Show clear option
                result = messagebox.askyesno(
                    "Ta bort utvisning",
                    f"Ta bort utvisning {slot}?"
                )
                if result:
                    try:
                        self.actions.clear_penalty(slot)
                    except Exception as e:
                        self.log(f"Error clearing penalty: {e}")
                return
        
        # Open dialog to set new penalty
        dialog = PenaltyDialog(self, self, slot)
        self.wait_window(dialog)
        
        if dialog.result:
            number, time_str = dialog.result
            try:
                self.actions.set_penalty(slot, number, time_str)
            except Exception as e:
                self.log(f"Error setting penalty: {e}")

    def _on_nameplate_click(self):
        """Handle nameplate button click"""
        if self.actions is None:
            return
        
        # If nameplate is currently visible, hide it
        if self.nameplate_visible:
            try:
                self.actions.hide_nameplate(logger=self.log)
                self.nameplate_visible = False
                self.nameplate_btn.config(
                    text="NAMNSKYLT",
                    bg="#9C27B0"
                )
                self.log("Nameplate: Hidden")
            except Exception as e:
                self.log(f"Error hiding nameplate: {e}")
            return
        
        # Open nameplate dialog
        dialog = NameplateDialog(self, self)
        self.wait_window(dialog)
        
        if dialog.result:
            team, person_type, number, name = dialog.result  # NEW FORMAT
            try:
                # Show nameplate
                self.actions.show_nameplate(person_type, number, name, team, logger=self.log)
                self.nameplate_visible = True
                self.nameplate_btn.config(
                    text="DÖLJ NAMNSKYLT",
                    bg="#E91E63"
                )
                self.log(f"Nameplate shown: {person_type} #{number} {name} ({team})")
            except Exception as e:
                self.log(f"Error showing nameplate: {e}")
    
    def _on_nameplate(self, team: str):
        """Quick nameplate access for specific team"""
        if self.actions is None:
            return
        
        # If nameplate is currently visible, hide it
        if self.nameplate_visible:
            try:
                self.actions.hide_nameplate(logger=self.log)
                self.nameplate_visible = False
                self.nameplate_btn.config(
                    text="NAMNSKYLT",
                    bg="#9C27B0"
                )
                self.log("Nameplate: Hidden")
            except Exception as e:
                self.log(f"Error hiding nameplate: {e}")
            return
        
        # Open nameplate dialog with pre-selected team
        dialog = NameplateDialog(self, self, default_team=team)
        self.wait_window(dialog)
        
        if dialog.result:
            team, person_type, number, name = dialog.result
            try:
                # Show nameplate
                self.actions.show_nameplate(person_type, number, name, team, logger=self.log)
                self.nameplate_visible = True
                self.nameplate_btn.config(
                    text="DÖLJ NAMNSKYLT",
                    bg="#E91E63"
                )
                self.log(f"Nameplate shown: {person_type} #{number} {name} ({team})")
            except Exception as e:
                self.log(f"Error showing nameplate: {e}")
                self.nameplate_btn.config(
                    text="DÖLJ NAMNSKYLT",
                    bg="#E91E63"
                )
                type_label = "Spelare" if person_type == "player" else "Ledare"
                if number:
                    self.log(f"Nameplate: {type_label} {team.upper()} - #{number} {name}")
                else:
                    self.log(f"Nameplate: {type_label} {team.upper()} - {name}")
            except Exception as e:
                self.log(f"Error showing nameplate: {e}")
                messagebox.showerror("Fel", f"Kunde inte visa namnskylt:\n{e}")

    # ========================================
    # Startup & vMix Connection
    # ========================================
    
    def _show_vmix_connection_dialog(self):
        """Show vMix connection dialog at startup"""
        from gui.dialogs import VMixConnectionDialog
        
        dialog = VMixConnectionDialog(self, self.config)
        self.wait_window(dialog)
        
        if dialog.result:
            # User provided vMix settings
            host, port, password = dialog.result
            
            # Update config
            if "vmix" not in self.config:
                self.config["vmix"] = {}
            self.config["vmix"]["host"] = host
            self.config["vmix"]["port"] = port
            self.config["vmix"]["password"] = password
            
            # Save to file
            try:
                import json
                with open("config.json", "w") as f:
                    json.dump(self.config, f, indent=2)
            except Exception as e:
                self.log(f"Could not save config: {e}")
            
            # Try to connect
            self._connect_to_vmix()
        else:
            # User cancelled - ask if they want to continue offline
            from tkinter import messagebox
            result = messagebox.askyesno(
                "Offline-läge?",
                "Vill du fortsätta utan vMix-anslutning?\n\n"
                "Du kan ansluta senare via ÅTERANSLUT-knappen."
            )
            
            if not result:
                self.destroy()
                sys.exit(0)
    
    def _connect_to_vmix(self):
        """Connect to vMix and start polling"""
        vmix_cfg = self.config.get("vmix", {})
        host = vmix_cfg.get("host", "127.0.0.1")
        port = vmix_cfg.get("port", 8088)
        password = vmix_cfg.get("password")
        
        try:
            self.log(f"Ansluter till vMix ({host}:{port})...")
            
            self.client = VMixClient(host, port, password)
            _ = self.client.get_status_xml()
            
            self.state_reader = StateReader(self.client, self.config)
            self.state_machine = StateMachine()
            self.actions = VMixActions(self.client, self.config)
            
            # Initialize Export Engine
            self.export_engine = ExportEngine(self.client, self.lineup_state)
            
            self.status_label.config(text="● Ansluten", fg="#2ecc71")
            self.log("● Ansluten till vMix")
            
            if not self.polling_active:
                self.polling_active = True
                self._poll()
            
        except Exception as e:
            self.status_label.config(text="Anslutning misslyckades", fg="#e74c3c")
            self.log(f"Fel vid anslutning: {e}")
            messagebox.showerror("Anslutningsfel", f"Kunde inte ansluta till vMix:\n{e}")

    # ========================================
    # Polling Loop
    # ========================================
    
    def _poll(self):
        """Polling loop"""
        if not self.polling_active:
            return
        
        try:
            game_state = self.state_reader.read_state()
            
            # Update state machine
            if game_state.clock_seconds is not None:
                clock_state = self.state_machine.update_clock(game_state.clock_seconds)
            else:
                clock_state = RunState.UNKNOWN
            
            # Update penalty states
            for slot, penalty in game_state.penalties.items():
                if penalty.seconds is not None:
                    self.state_machine.update_penalty(slot, penalty.seconds)
            
            # Auto-clear penalties
            self._auto_clear_penalties(game_state)
            
            # Check for period end
            self._check_period_end(game_state, clock_state)
            
            # Update UI
            self._update_ui(game_state, clock_state)
            
            self.last_game_state = game_state
            
        except Exception as e:
            self.log(f"Polling error: {e}")
            self.status_label.config(text="âš  Polling-fel", fg="#f39c12")
        
        self.after(self.poll_interval, self._poll)

    def _auto_clear_penalties(self, game_state):
        """Auto-clear penalties at 00:00"""
        if not game_state or not self.actions:
            return
        
        # Don't clear at period end
        if game_state.clock_seconds is not None and game_state.clock_seconds <= 1:
            return
        
        for slot, penalty in game_state.penalties.items():
            current_secs = penalty.seconds if penalty.seconds is not None else 0
            last_secs = self.last_penalty_seconds.get(slot, None)
            
            if current_secs == 0 and (last_secs is None or last_secs > 0):
                if penalty.number and penalty.number.strip():
                    try:
                        self.log(f"Auto-clearing expired penalty: {slot}")
                        self.actions.clear_penalty(slot)
                    except Exception as e:
                        self.log(f"Error auto-clearing penalty {slot}: {e}")
            
            self.last_penalty_seconds[slot] = current_secs

    def _check_period_end(self, game_state, clock_state):
        """Check for period end"""
        if game_state.clock_seconds != 1:
            self.period_end_shown = False
            return
        
        if self.period_end_shown:
            return
        
        self.period_end_shown = True
        self.log("Period end detected at 00:01")
        
        # Pause everything
        try:
            self.actions.pause_clock()
            for slot in ["H1", "H2", "A1", "A2"]:
                penalty = game_state.penalties.get(slot)
                if penalty and penalty.active:
                    self.actions.pause_penalty(slot)
        except Exception as e:
            self.log(f"Error pausing at period end: {e}")
        
        # Auto-hide scoreboard
        if game_state.scoreboard_visible:
            try:
                self.actions.hide_scoreboard()
                self.log("Auto-hide scoreboard at period end")
            except Exception as e:
                self.log(f"Error hiding scoreboard: {e}")
        
        # Show dialog after 1 second
        def show_dialog():
            current_period = game_state.period
            dialog = PeriodEndDialog(self, current_period)
            self.wait_window(dialog)
            
            if dialog.result:
                self._advance_period(current_period)
            else:
                try:
                    self.actions.show_scoreboard()
                    self.log("Period end: NEJ - clock paused at 00:01")
                except Exception as e:
                    self.log(f"Error: {e}")
        
        self.after(1000, show_dialog)

    def _advance_period(self, current_period: str):
        """Advance to next period"""
        try:
            if self.last_game_state:
                for slot, penalty in self.last_game_state.penalties.items():
                    if penalty.active:
                        self.actions.pause_penalty(slot)
            
            periods_cfg = self.config.get("periods", {})
            period_map = {
                "1": ("2", periods_cfg.get("P2_duration", "20:00")),
                "2": ("3", periods_cfg.get("P3_duration", "20:00")),
                "3": ("OT", periods_cfg.get("OT_duration", "05:00")),
            }
            
            next_period, next_time = period_map.get(current_period, ("1", "20:00"))
            
            self.actions.set_period(next_period)
            self.actions.set_clock_time(next_time)
            
            self.log(f"Period {current_period} â†’ {next_period} ({next_time})")
            
            self.after(1000, lambda: setattr(self, 'period_end_shown', False))
            
        except Exception as e:
            self.log(f"Error advancing period: {e}")

    # ========================================
    # UI Updates
    # ========================================
    
    def _update_ui(self, game_state, clock_state):
        """Update all UI elements"""
        # Clock
        self.time_display.config(text=game_state.clock_raw)
        
        if clock_state == RunState.RUNNING:
            self.clock_toggle_btn.config(text="PAUS", bg="red", fg="white")
        else:
            self.clock_toggle_btn.config(text="START", bg="green", fg="white")
        
        # Enable/disable adjustment buttons
        current_secs = game_state.clock_seconds if game_state.clock_seconds else 0
        
        if current_secs >= 7:
            self.adj_minus5.config(state=tk.NORMAL)
        else:
            self.adj_minus5.config(state=tk.DISABLED)
        
        if current_secs >= 3:
            self.adj_minus1.config(state=tk.NORMAL)
        else:
            self.adj_minus1.config(state=tk.DISABLED)
        
        # Goals
        self.home_goal_btn.config(text=f"MÅL\n{game_state.home_score}")
        self.away_goal_btn.config(text=f"MÅL\n{game_state.away_score}")
        
        # Scoreboard
        if game_state.scoreboard_visible:
            self.scoreboard_btn.config(text="DÖLJ SCOREBOARD", bg="#3498db", fg="white")
        else:
            self.scoreboard_btn.config(text="VISA SCOREBOARD", bg="#bdc3c7", fg="black")
        
        # Period highlighting
        current_period = game_state.period
        for period_val, btn in self.period_buttons.items():
            if str(period_val) == str(current_period):
                # Active period - highlight
                btn.config(relief='sunken', bg='#4CAF50', fg='white')
            else:
                # Inactive period - normal
                btn.config(relief='raised', bg='white', fg='black')
        
        # Penalties
        for slot, btn in self.penalty_buttons.items():
            penalty = game_state.penalties.get(slot)
            if penalty:
                text = f"{slot}\n{penalty.time_raw}\n{penalty.number}"
                btn.config(text=text)
                
                if penalty.active:
                    btn.config(bg="#f1c40f", fg="black")
                else:
                    btn.config(bg="white", fg="black")
            else:
                btn.config(text=f"{slot}\n00:00\n", bg="white", fg="black")

    def _update_empty_goal_buttons(self):
        """Update empty goal button colors"""
        self.empty_home_btn.config(
            bg="#3498db" if self.home_empty_active else "white",
            fg="white" if self.home_empty_active else "black"
        )
        self.empty_away_btn.config(
            bg="#3498db" if self.away_empty_active else "white",
            fg="white" if self.away_empty_active else "black"
        )

    # ========================================
    # API Import
    # ========================================
    
    def _on_import_from_api(self):
        """Import lineup from Hockeyettan API"""
        from gui.api_lineup_dialog import ApiLineupDialog
        from gui.lineup_preview_dialog import LineupPreviewDialog
        
        # Open API dialog
        dialog = ApiLineupDialog(self, self.data_manager)
        self.wait_window(dialog)
        
        if dialog.result:
            # Write logos to scoreboard IMMEDIATELY (before preview)
            self._write_logos_to_scoreboard(dialog.result)
            
            # Show preview
            preview = LineupPreviewDialog(
                self,
                dialog.result,
                source_info="Hockeyettan API"
            )
            self.wait_window(preview)
            
            if preview.result == 'accept':
                # Store lineup in DataManager
                self.data_manager.set_current_lineup(dialog.result)
                
                # Store in centralized LineupState for export
                self.lineup_state.update_from_lineup_data(dialog.result)
                
                # Initialize JSON Exporter
                self.json_exporter = JSONExporter(self.lineup_state)
                
                self.log("✓ Lineup från API godkänd och sparad")
            elif preview.result == 'reload':
                # User wants to reload - call this method again
                self._on_import_from_api()
    
    def _write_logos_to_scoreboard(self, lineup_data):
        """Write team names and logos to scoreboard after API import"""
        try:
            # Get data from lineup
            home_name = lineup_data.home_team.get('name', '')
            away_name = lineup_data.away_team.get('name', '')
            home_logo = lineup_data.home_team.get('logo', '')
            away_logo = lineup_data.away_team.get('logo', '')
            
            if not any([home_name, away_name, home_logo, away_logo]):
                return  # Nothing to write
            
            # Get scoreboard config
            sb_cfg = self.config.get("scoreboard", {})
            sb_input = sb_cfg.get("input", "")
            
            home_name_field = sb_cfg.get("home_name_field", "HomeName.Text")
            away_name_field = sb_cfg.get("away_name_field", "AwayName.Text")
            home_logo_field = sb_cfg.get("home_logo_field", "HomeLogo.Source")
            away_logo_field = sb_cfg.get("away_logo_field", "AwayLogo.Source")
            
            # Get scoreboard input number
            sb_num = self.client.find_input_number(sb_input)
            if not sb_num:
                self.log("⚠ Kunde inte hitta scoreboard för att skriva lag-info")
                return
            
            # Write team names
            if home_name:
                self.client.set_text(sb_num, home_name_field, home_name)
                self.log(f"✓ Hemmalag: {home_name}")
            
            if away_name:
                self.client.set_text(sb_num, away_name_field, away_name)
                self.log(f"✓ Bortalag: {away_name}")
            
            # Write logos
            if home_logo:
                self.client.set_text(sb_num, home_logo_field, home_logo)
                self.log(f"✓ Hemma-logo: {home_logo}")
            
            if away_logo:
                self.client.set_text(sb_num, away_logo_field, away_logo)
                self.log(f"✓ Borta-logo: {away_logo}")
                
        except Exception as e:
            self.log(f"⚠ Kunde inte skriva lag-info: {e}")
    
    # ========================================
    # Utilities
    # ========================================
    
    def log(self, message: str):
        """Add message to log"""
        timestamp = datetime.now().strftime("%H:%M:%S")
        log_msg = f"[{timestamp}] {message}\n"
        
        self.log_text.config(state=tk.NORMAL)
        self.log_text.insert(tk.END, log_msg)
        self.log_text.see(tk.END)
        self.log_text.config(state=tk.DISABLED)

    def on_closing(self):
        """Handle window close"""
        self.polling_active = False
        self.destroy()

    def _open_settings(self):
        """Open settings window"""
        settings = SettingsWindow(self, self.config, self.client)
        self.wait_window(settings)
        
        if settings.result:
            messagebox.showinfo(
                "Inställningar sparade",
                "Inställningarna har sparats.\n\nStarta om applikationen för att ändringarna ska träda i kraft."
            )
