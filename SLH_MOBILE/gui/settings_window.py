# gui/settings_window.py
"""
Settings Window for SLH - MED DROPDOWNS
Allows user to configure all vMix mappings and settings
"""

import tkinter as tk
from tkinter import ttk, messagebox
import json
from pathlib import Path
from typing import Dict, List, Optional


class SettingsWindow(tk.Toplevel):
    """
    Complete settings window with DROPDOWNS for all vMix fields.
    """

    def __init__(self, parent, config: dict, vmix_client=None):
        super().__init__(parent)
        
        self.parent = parent
        self.config = config.copy()  # Work on a copy
        self.vmix_client = vmix_client
        self.result = None
        
        self.title("Inställningar - SLH")
        self.geometry("800x800")  # Taller window
        self.resizable(True, True)
        
        # Available inputs from vMix
        self.available_inputs = []
        self.available_text_fields = {}
        self.available_image_fields = {}
        
        if self.vmix_client:
            self._fetch_vmix_data()
        
        self._build_ui()
        
        # Make modal
        self.transient(parent)
        self.grab_set()

    def _fetch_vmix_data(self):
        """Fetch available inputs and fields from vMix"""
        try:
            root = self.vmix_client.get_status_xml()
            
            # Get all inputs
            for inp in root.findall("./inputs/input"):
                title = inp.get("title", "").strip()
                if title:
                    self.available_inputs.append(title)
                    
                    # Get text fields from <text> tags
                    text_fields = []
                    for txt in inp.findall("./text"):
                        name = txt.get("name", "")
                        if name and name.endswith(".Text"):
                            text_fields.append(name)
                    
                    # Get image fields from <image> tags (NOT from <text>!)
                    image_fields = []
                    for img in inp.findall("./image"):
                        name = img.get("name", "")
                        if name and name.endswith(".Source"):
                            image_fields.append(name)
                    
                    if text_fields:
                        self.available_text_fields[title] = sorted(text_fields)
                    if image_fields:
                        self.available_image_fields[title] = sorted(image_fields)
            
            self.available_inputs.sort()
            
        except Exception as e:
            messagebox.showwarning(
                "vMix-fel",
                f"Kunde inte hämta inputs från vMix:\n{e}\n\nDu kan fortfarande mata in namn manuellt."
            )

    def _build_ui(self):
        """Build settings UI"""
        
        # Create notebook (tabs)
        notebook = ttk.Notebook(self)
        notebook.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        # Tabs
        self._build_vmix_tab(notebook)
        self._build_links_tab(notebook)      # NEW: Links/folders settings
        self._build_scoreboard_tab(notebook)
        self._build_penalties_tab(notebook)
        self._build_goal_graphics_tab(notebook)
        self._build_lineup_tab(notebook)     # NEW v4.3: Editable lineup
        self._build_nameplate_tab(notebook)
        # REMOVED: images_tab and export_tab (integrated in lineup now)
        
        # Bottom buttons
        btn_frame = tk.Frame(self, bg="#ecf0f1")
        btn_frame.pack(fill=tk.X, padx=10, pady=10)
        
        tk.Button(
            btn_frame,
            text="Spara",
            width=15,
            font=("Segoe UI", 10, "bold"),
            bg="#4CAF50",
            fg="white",
            command=self._on_save
        ).pack(side=tk.RIGHT, padx=5)
        
        tk.Button(
            btn_frame,
            text="Avbryt",
            width=15,
            font=("Segoe UI", 10),
            command=self.destroy
        ).pack(side=tk.RIGHT, padx=5)
        
        tk.Button(
            btn_frame,
            text="Testa anslutning",
            width=18,
            font=("Segoe UI", 10),
            command=self._test_connection
        ).pack(side=tk.LEFT, padx=5)

    # ========================================
    # TAB 1: vMix Connection
    # ========================================
    def _build_vmix_tab(self, notebook):
        """vMix connection settings"""
        frame = ttk.Frame(notebook)
        notebook.add(frame, text="vMix Anslutning")
        
        # Create scrollable frame
        canvas = tk.Canvas(frame)
        scrollbar = ttk.Scrollbar(frame, orient="vertical", command=canvas.yview)
        scrollable = ttk.Frame(canvas)
        
        scrollable.bind(
            "<Configure>",
            lambda e: canvas.configure(scrollregion=canvas.bbox("all"))
        )
        
        canvas.create_window((0, 0), window=scrollable, anchor="nw")
        canvas.configure(yscrollcommand=scrollbar.set)
        
        canvas.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        
        # Content
        content = ttk.Frame(scrollable, padding=20)
        content.pack(fill=tk.BOTH, expand=True)
        
        vmix_cfg = self.config.get("vmix", {})
        
        # Host
        ttk.Label(content, text="Host / IP:", font=("Segoe UI", 10, "bold")).grid(
            row=0, column=0, sticky=tk.W, pady=5
        )
        self.vmix_host = tk.Entry(content, width=30)
        self.vmix_host.insert(0, vmix_cfg.get("host", "127.0.0.1"))
        self.vmix_host.grid(row=0, column=1, sticky=tk.W, padx=10, pady=5)
        
        # Port
        ttk.Label(content, text="Port:", font=("Segoe UI", 10, "bold")).grid(
            row=1, column=0, sticky=tk.W, pady=5
        )
        self.vmix_port = tk.Entry(content, width=10)
        self.vmix_port.insert(0, str(vmix_cfg.get("port", 8088)))
        self.vmix_port.grid(row=1, column=1, sticky=tk.W, padx=10, pady=5)
        
        # Password (optional)
        ttk.Label(content, text="Lösenord (valfritt):", font=("Segoe UI", 10, "bold")).grid(
            row=2, column=0, sticky=tk.W, pady=5
        )
        self.vmix_password = tk.Entry(content, width=30, show="*")
        if vmix_cfg.get("password"):
            self.vmix_password.insert(0, vmix_cfg.get("password"))
        self.vmix_password.grid(row=2, column=1, sticky=tk.W, padx=10, pady=5)

    # ========================================
    # TAB 2: Scoreboard
    # ========================================
    def _build_scoreboard_tab(self, notebook):
        """Scoreboard mapping with DROPDOWNS"""
        frame = ttk.Frame(notebook)
        notebook.add(frame, text="Scoreboard")
        
        canvas = tk.Canvas(frame)
        scrollbar = ttk.Scrollbar(frame, orient="vertical", command=canvas.yview)
        scrollable = ttk.Frame(canvas)
        
        scrollable.bind(
            "<Configure>",
            lambda e: canvas.configure(scrollregion=canvas.bbox("all"))
        )
        
        canvas.create_window((0, 0), window=scrollable, anchor="nw")
        canvas.configure(yscrollcommand=scrollbar.set)
        
        canvas.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        
        content = ttk.Frame(scrollable, padding=20)
        content.pack(fill=tk.BOTH, expand=True)
        
        sb_cfg = self.config.get("scoreboard", {})
        
        row = 0
        
        # Scoreboard Input
        ttk.Label(content, text="Scoreboard Input:", font=("Segoe UI", 11, "bold")).grid(
            row=row, column=0, columnspan=2, sticky=tk.W, pady=(0, 10)
        )
        row += 1
        
        self.sb_input = self._create_input_dropdown(
            content, row, "Input:", sb_cfg.get("input", "")
        )
        row += 1
        
        ttk.Label(content, text="Overlay kanal (1-8):", font=("Segoe UI", 10)).grid(
            row=row, column=0, sticky=tk.W, pady=5
        )
        self.sb_overlay_channel = tk.Spinbox(content, from_=1, to=8, width=5)
        self.sb_overlay_channel.delete(0, tk.END)
        self.sb_overlay_channel.insert(0, str(sb_cfg.get("overlay_channel", 1)))
        self.sb_overlay_channel.grid(row=row, column=1, sticky=tk.W, padx=10, pady=5)
        row += 1
        
        # Separator
        ttk.Separator(content, orient=tk.HORIZONTAL).grid(
            row=row, column=0, columnspan=2, sticky=tk.EW, pady=15
        )
        row += 1
        
        # Field mappings
        ttk.Label(content, text="Fältmappningar:", font=("Segoe UI", 11, "bold")).grid(
            row=row, column=0, columnspan=2, sticky=tk.W, pady=(0, 10)
        )
        row += 1
        
        # Create field selectors with DROPDOWNS
        self.sb_fields = {}
        field_mappings = [
            ("clock_field", "Matchklocka (Time.Text):", "Time.Text", "text"),
            ("home_score_field", "Hemma mål:", "HomeScore.Text", "text"),
            ("away_score_field", "Borta mål:", "AwayScore.Text", "text"),
            ("home_name_field", "Hemma lagnamn:", "HomeName.Text", "text"),
            ("away_name_field", "Borta lagnamn:", "AwayName.Text", "text"),
            ("home_logo_field", "Hemma logotyp:", "HomeLogo.Source", "image"),
            ("away_logo_field", "Borta logotyp:", "AwayLogo.Source", "image"),
            ("period_field", "Period:", "PeriodNr.Text", "text"),
            ("home_empty_field", "Tom målbur hemma (text):", "EmptyGoalH.Text", "text"),
            ("home_empty_bg_field", "Tom målbur hemma (bg):", "EmptyGoalHbg.Source", "image"),
            ("away_empty_field", "Tom målbur borta (text):", "EmptyGoalA.Text", "text"),
            ("away_empty_bg_field", "Tom målbur borta (bg):", "EmptyGoalAbg.Source", "image"),
        ]
        
        for field_key, label, default, field_type in field_mappings:
            combo = self._create_field_dropdown(
                content, row, label,
                sb_cfg.get(field_key, default),
                field_type=field_type
            )
            self.sb_fields[field_key] = combo
            row += 1
        
        # NEW: Separator for SCOREBOARD NERE
        ttk.Separator(content, orient=tk.HORIZONTAL).grid(
            row=row, column=0, columnspan=2, sticky=tk.EW, pady=20
        )
        row += 1
        
        # NEW: SCOREBOARD NERE Section
        ttk.Label(content, text="SCOREBOARD NERE (Fullständiga namn + stora logos):", 
                  font=("Segoe UI", 11, "bold")).grid(
            row=row, column=0, columnspan=2, sticky=tk.W, pady=(0, 10)
        )
        row += 1
        
        # SCOREBOARD NERE input
        sb_nere_cfg = self.config.get("scoreboard_nere", {})
        
        self.sb_nere_input = self._create_input_dropdown(
            content, row, "Input:", sb_nere_cfg.get("input", "SCOREBOARD NERE")
        )
        row += 1
        
        ttk.Label(content, text="Overlay kanal (1-8):", font=("Segoe UI", 10)).grid(
            row=row, column=0, sticky=tk.W, pady=5
        )
        self.sb_nere_overlay = tk.Spinbox(content, from_=1, to=8, width=5)
        self.sb_nere_overlay.delete(0, tk.END)
        self.sb_nere_overlay.insert(0, str(sb_nere_cfg.get("overlay_channel", 1)))
        self.sb_nere_overlay.grid(row=row, column=1, sticky=tk.W, padx=10, pady=5)
        row += 1
        
        # SCOREBOARD NERE field mappings
        self.sb_nere_fields = {}
        nere_field_mappings = [
            ("home_name_field", "Hemma fullständigt namn:", "HomeName.Text", "text"),
            ("away_name_field", "Borta fullständigt namn:", "AwayName.Text", "text"),
            ("home_logo_big_field", "Hemma stor logotyp:", "LogoHome.Source", "image"),
            ("away_logo_big_field", "Borta stor logotyp:", "LogoAway.Source", "image"),
            ("home_logo_small_field", "Hemma liten logotyp:", "HomeLogo.Source", "image"),
            ("away_logo_small_field", "Borta liten logotyp:", "AwayLogo.Source", "image"),
        ]
        
        for field_key, label, default, field_type in nere_field_mappings:
            combo = self._create_field_dropdown(
                content, row, label,
                sb_nere_cfg.get(field_key, default),
                field_type=field_type
            )
            self.sb_nere_fields[field_key] = combo
            row += 1

    # ========================================
    # TAB 3: Penalties
    # ========================================
    def _build_penalties_tab(self, notebook):
        """Penalty slot mappings with DROPDOWNS"""
        frame = ttk.Frame(notebook)
        notebook.add(frame, text="Utvisningar")
        
        canvas = tk.Canvas(frame)
        scrollbar = ttk.Scrollbar(frame, orient="vertical", command=canvas.yview)
        scrollable = ttk.Frame(canvas)
        
        scrollable.bind(
            "<Configure>",
            lambda e: canvas.configure(scrollregion=canvas.bbox("all"))
        )
        
        canvas.create_window((0, 0), window=scrollable, anchor="nw")
        canvas.configure(yscrollcommand=scrollbar.set)
        
        canvas.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        
        content = ttk.Frame(scrollable, padding=20)
        content.pack(fill=tk.BOTH, expand=True)
        
        pen_cfg = self.config.get("scoreboard", {}).get("penalties", {})
        
        self.penalty_fields = {}
        
        slots = ["H1", "H2", "A1", "A2"]
        slot_names = {
            "H1": "HomeP1",
            "H2": "HomeP2",
            "A1": "AwayP1",
            "A2": "AwayP2"
        }
        
        row = 0
        
        for slot in slots:
            slot_name = slot_names[slot]
            slot_cfg = pen_cfg.get(slot, {})
            
            # Section header
            ttk.Label(content, text=f"Slot {slot}:", font=("Segoe UI", 11, "bold")).grid(
                row=row, column=0, columnspan=2, sticky=tk.W, pady=(10, 5)
            )
            row += 1
            
            # Time field (text) - DROPDOWN
            time_combo = self._create_field_dropdown(
                content, row, "Tid-fält:",
                slot_cfg.get("time_field", f"{slot_name}time.Text"),
                field_type="text"
            )
            row += 1
            
            # Number field (text) - DROPDOWN
            number_combo = self._create_field_dropdown(
                content, row, "Nummer-fält:",
                slot_cfg.get("number_field", f"{slot_name}nr.Text"),
                field_type="text"
            )
            row += 1
            
            # Time BG field (image) - DROPDOWN
            time_bg_combo = self._create_field_dropdown(
                content, row, "Tid BG-fält:",
                slot_cfg.get("time_bg_field", f"{slot_name}bg.Source"),
                field_type="image"
            )
            row += 1
            
            # Number BG field (image) - DROPDOWN
            number_bg_combo = self._create_field_dropdown(
                content, row, "Nummer BG-fält:",
                slot_cfg.get("number_bg_field", f"{slot_name}bgnr.Source"),
                field_type="image"
            )
            row += 1
            
            # Store references
            self.penalty_fields[slot] = {
                "time_field": time_combo,
                "number_field": number_combo,
                "time_bg_field": time_bg_combo,
                "number_bg_field": number_bg_combo
            }
            
            # Separator
            ttk.Separator(content, orient=tk.HORIZONTAL).grid(
                row=row, column=0, columnspan=2, sticky=tk.EW, pady=10
            )
            row += 1

    # ========================================
    # TAB 4: Goal Graphics
    # ========================================
    def _build_goal_graphics_tab(self, notebook):
        """Goal graphic settings with DROPDOWNS"""
        frame = ttk.Frame(notebook)
        notebook.add(frame, text="Målgrafik")
        
        canvas = tk.Canvas(frame)
        scrollbar = ttk.Scrollbar(frame, orient="vertical", command=canvas.yview)
        scrollable = ttk.Frame(canvas)
        
        scrollable.bind(
            "<Configure>",
            lambda e: canvas.configure(scrollregion=canvas.bbox("all"))
        )
        
        canvas.create_window((0, 0), window=scrollable, anchor="nw")
        canvas.configure(yscrollcommand=scrollbar.set)
        
        canvas.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        
        content = ttk.Frame(scrollable, padding=20)
        content.pack(fill=tk.BOTH, expand=True)
        
        goal_cfg = self.config.get("goal_graphic", {})
        after_cfg = self.config.get("after_goal_graphic", {})
        
        row = 0
        
        # Goal Graphic
        ttk.Label(content, text="Målgrafik (MÅÅÅL):", font=("Segoe UI", 11, "bold")).grid(
            row=row, column=0, columnspan=2, sticky=tk.W, pady=(0, 10)
        )
        row += 1
        
        self.goal_input = self._create_input_dropdown(
            content, row, "Input:", goal_cfg.get("input", "")
        )
        row += 1
        
        ttk.Label(content, text="Overlay kanal:", font=("Segoe UI", 9)).grid(
            row=row, column=0, sticky=tk.W, pady=3
        )
        self.goal_overlay = tk.Spinbox(content, from_=1, to=8, width=5)
        self.goal_overlay.delete(0, tk.END)
        self.goal_overlay.insert(0, str(goal_cfg.get("overlay_channel", 2)))
        self.goal_overlay.grid(row=row, column=1, sticky=tk.W, padx=10, pady=3)
        row += 1
        
        ttk.Label(content, text="Varaktighet (ms):", font=("Segoe UI", 9)).grid(
            row=row, column=0, sticky=tk.W, pady=3
        )
        self.goal_duration = tk.Entry(content, width=10)
        self.goal_duration.insert(0, str(goal_cfg.get("duration_ms", 5000)))
        self.goal_duration.grid(row=row, column=1, sticky=tk.W, padx=10, pady=3)
        row += 1
        
        # Separator
        ttk.Separator(content, orient=tk.HORIZONTAL).grid(
            row=row, column=0, columnspan=2, sticky=tk.EW, pady=15
        )
        row += 1
        
        # After Goal Graphic
        ttk.Label(content, text="After Goal (Namnskylt):", font=("Segoe UI", 11, "bold")).grid(
            row=row, column=0, columnspan=2, sticky=tk.W, pady=(0, 10)
        )
        row += 1
        
        self.after_goal_input = self._create_input_dropdown(
            content, row, "Input:", after_cfg.get("input", "")
        )
        row += 1
        
        ttk.Label(content, text="Overlay kanal:", font=("Segoe UI", 9)).grid(
            row=row, column=0, sticky=tk.W, pady=3
        )
        self.after_goal_overlay = tk.Spinbox(content, from_=1, to=8, width=5)
        self.after_goal_overlay.delete(0, tk.END)
        self.after_goal_overlay.insert(0, str(after_cfg.get("overlay_channel", 2)))
        self.after_goal_overlay.grid(row=row, column=1, sticky=tk.W, padx=10, pady=3)
        row += 1
        
        ttk.Label(content, text="Varaktighet (ms):", font=("Segoe UI", 9)).grid(
            row=row, column=0, sticky=tk.W, pady=3
        )
        self.after_goal_duration = tk.Entry(content, width=10)
        self.after_goal_duration.insert(0, str(after_cfg.get("duration_ms", 4000)))
        self.after_goal_duration.grid(row=row, column=1, sticky=tk.W, padx=10, pady=3)
        row += 1
        
        ttk.Label(content, text="Paus innan (ms):", font=("Segoe UI", 9)).grid(
            row=row, column=0, sticky=tk.W, pady=3
        )
        self.after_goal_pause = tk.Entry(content, width=10)
        self.after_goal_pause.insert(0, str(after_cfg.get("pause_before_ms", 2000)))
        self.after_goal_pause.grid(row=row, column=1, sticky=tk.W, padx=10, pady=3)
        row += 1
        
        # Text fields for After Goal nameplate
        ttk.Label(
            content,
            text="Text-fält för After Goal namnskylt:",
            font=("Segoe UI", 10, "bold")
        ).grid(row=row, column=0, columnspan=2, sticky=tk.W, pady=(10, 5))
        row += 1
        
        self.after_goal_number_field = self._create_field_dropdown(
            content, row, "Nummer (ShirtNr):", after_cfg.get("number_field", "ShirtNr.Text"),
            self.after_goal_input
        )
        row += 1
        
        self.after_goal_name_field = self._create_field_dropdown(
            content, row, "Namn (Name):", after_cfg.get("name_field", "Name.Text"),
            self.after_goal_input
        )
        row += 1
        
        self.after_goal_team_field = self._create_field_dropdown(
            content, row, "Lagnamn (Team):", after_cfg.get("team_field", "Team.Text"),
            self.after_goal_input
        )
        row += 1
        
        self.after_goal_logo_field = self._create_field_dropdown(
            content, row, "Logotyp (Logo):", after_cfg.get("logo_field", "Logo.Source"),
            self.after_goal_input, is_image=True
        )
        row += 1

    # ========================================
    # TAB 5: Lineup
    # ========================================
    def _build_lineup_tab(self, notebook):
        """NEW v4.3: Lineup editor with editable tables"""
        from gui.lineup_editor import LineupEditor
        
        # Create LineupEditor component
        editor = LineupEditor(notebook, self.config, None, self.vmix_client)
        notebook.add(editor, text="Lineup")
        
        # Store reference for export
        self.lineup_editor = editor
        """Lineup input settings with DROPDOWNS"""
        frame = ttk.Frame(notebook)
        notebook.add(frame, text="Laguppställningar")
        
        canvas = tk.Canvas(frame)
        scrollbar = ttk.Scrollbar(frame, orient="vertical", command=canvas.yview)
        scrollable = ttk.Frame(canvas)
        
        scrollable.bind(
            "<Configure>",
            lambda e: canvas.configure(scrollregion=canvas.bbox("all"))
        )
        
        canvas.create_window((0, 0), window=scrollable, anchor="nw")
        canvas.configure(yscrollcommand=scrollbar.set)
        
        canvas.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        
        content = ttk.Frame(scrollable, padding=20)
        content.pack(fill=tk.BOTH, expand=True)
        
        lineup_cfg = self.config.get("lineup", {})
        
        row = 0
        
        self.lineup_home = self._create_input_dropdown(
            content, row, "LINEUP HEMMA:", lineup_cfg.get("home_input", "")
        )
        row += 1
        
        self.lineup_away = self._create_input_dropdown(
            content, row, "LINEUP BORTA:", lineup_cfg.get("away_input", "")
        )

    # ========================================
    # TAB 6: NAMEPLATE (NAMNSKYLT)
    # ========================================
    def _build_nameplate_tab(self, notebook):
        """Nameplate settings with DROPDOWNS for player and staff graphics"""
        frame = ttk.Frame(notebook)
        notebook.add(frame, text="Namnskyltar")
        
        canvas = tk.Canvas(frame)
        scrollbar = ttk.Scrollbar(frame, orient="vertical", command=canvas.yview)
        scrollable = ttk.Frame(canvas)
        
        scrollable.bind(
            "<Configure>",
            lambda e: canvas.configure(scrollregion=canvas.bbox("all"))
        )
        
        canvas.create_window((0, 0), window=scrollable, anchor="nw")
        canvas.configure(yscrollcommand=scrollbar.set)
        
        canvas.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        
        content = ttk.Frame(scrollable, padding=20)
        content.pack(fill=tk.BOTH, expand=True)
        
        np_cfg = self.config.get("nameplate", {})
        
        row = 0
        
        # SECTION: Spelare (Players)
        ttk.Label(
            content,
            text="NAMNSKYLT MED NUMMER (SPELARE):",
            font=("Segoe UI", 11, "bold"),
            foreground="#2196F3"
        ).grid(row=row, column=0, columnspan=3, sticky=tk.W, pady=(0, 10))
        row += 1
        
        # Player input
        self.nameplate_player_input = self._create_input_dropdown(
            content, row, "Input:", np_cfg.get("player_input", "")
        )
        row += 1
        
        # Overlay channel
        ttk.Label(content, text="Overlay Channel:", font=("Segoe UI", 10)).grid(
            row=row, column=0, sticky=tk.W, pady=5
        )
        self.nameplate_overlay_channel = ttk.Entry(content, width=10)
        self.nameplate_overlay_channel.insert(0, str(np_cfg.get("overlay_channel", 3)))
        self.nameplate_overlay_channel.grid(row=row, column=1, sticky=tk.W, padx=10, pady=5)
        row += 1
        
        # Player fields
        ttk.Label(
            content,
            text="Text-fält för SPELARE:",
            font=("Segoe UI", 10, "bold")
        ).grid(row=row, column=0, columnspan=2, sticky=tk.W, pady=(10, 5))
        row += 1
        
        self.nameplate_number_field = self._create_field_dropdown(
            content, row, "Nummer (ShirtNr):", np_cfg.get("number_field", ""),
            self.nameplate_player_input
        )
        row += 1
        
        self.nameplate_name_field = self._create_field_dropdown(
            content, row, "Namn (Name):", np_cfg.get("name_field", ""),
            self.nameplate_player_input
        )
        row += 1
        
        self.nameplate_team_field = self._create_field_dropdown(
            content, row, "Lagnamn (Team):", np_cfg.get("team_field", ""),
            self.nameplate_player_input
        )
        row += 1
        
        self.nameplate_logo_field = self._create_field_dropdown(
            content, row, "Logotyp (Logo):", np_cfg.get("logo_field", ""),
            self.nameplate_player_input, is_image=True
        )
        row += 1
        
        # SEPARATOR
        ttk.Separator(content, orient="horizontal").grid(
            row=row, column=0, columnspan=3, sticky="ew", pady=20
        )
        row += 1
        
        # SECTION: Ledare (Staff)
        ttk.Label(
            content,
            text="NAMNSKYLT LEDARE (UTAN NUMMER):",
            font=("Segoe UI", 11, "bold"),
            foreground="#E91E63"
        ).grid(row=row, column=0, columnspan=3, sticky=tk.W, pady=(0, 10))
        row += 1
        
        # Staff input
        self.nameplate_staff_input = self._create_input_dropdown(
            content, row, "Input:", np_cfg.get("staff_input", "")
        )
        row += 1
        
        # Staff fields
        ttk.Label(
            content,
            text="Text-fält för LEDARE:",
            font=("Segoe UI", 10, "bold")
        ).grid(row=row, column=0, columnspan=2, sticky=tk.W, pady=(10, 5))
        row += 1
        
        self.nameplate_staff_name_field = self._create_field_dropdown(
            content, row, "Namn (Name):", np_cfg.get("staff_name_field", ""),
            self.nameplate_staff_input
        )
        row += 1
        
        self.nameplate_staff_role_field = self._create_field_dropdown(
            content, row, "Titel/Roll:", np_cfg.get("staff_role_field", "Titel.Text"),
            self.nameplate_staff_input
        )
        row += 1
        
        self.nameplate_staff_team_field = self._create_field_dropdown(
            content, row, "Lagnamn (Team):", np_cfg.get("staff_team_field", ""),
            self.nameplate_staff_input
        )
        row += 1
        
        self.nameplate_staff_logo_field = self._create_field_dropdown(
            content, row, "Logotyp (Logo):", np_cfg.get("staff_logo_field", ""),
            self.nameplate_staff_input, is_image=True
        )

    # ========================================
    # Helper: Input Dropdown
    # ========================================
    def _create_input_dropdown(self, parent, row, label, current_value):
        """Create a DROPDOWN for selecting vMix input"""
        ttk.Label(parent, text=label, font=("Segoe UI", 10, "bold")).grid(
            row=row, column=0, sticky=tk.W, pady=5
        )
        
        # Combo box with available inputs
        values = ["NONE"] + self.available_inputs
        combo = ttk.Combobox(parent, width=35, values=values)
        
        if current_value:
            combo.set(current_value)
        else:
            combo.set("NONE")
        
        combo.grid(row=row, column=1, sticky=tk.W, padx=10, pady=5)
        
        return combo

    def _create_field_dropdown(self, parent, row, label, current_value, input_combo=None, is_image=False, field_type=None):
        """
        Create a DROPDOWN for selecting vMix text/image field.
        
        BACKWARD COMPATIBLE - supports both old and new calling styles:
        - OLD: _create_field_dropdown(parent, row, label, value, field_type="text/image")
        - NEW: _create_field_dropdown(parent, row, label, value, input_combo, is_image=True/False)
        
        Args:
            input_combo: The combobox containing the input name (NEW style)
            is_image: True for .Source fields, False for .Text fields (NEW style)
            field_type: "text" or "image" (OLD style - DEPRECATED)
        """
        ttk.Label(parent, text=label, font=("Segoe UI", 9)).grid(
            row=row, column=0, sticky=tk.W, pady=3
        )
        
        # BACKWARD COMPATIBILITY: Convert old field_type to new is_image
        if field_type is not None:
            # OLD STYLE CALL (from scoreboard/penalties)
            is_image = (field_type == "image")
            # Use scoreboard input as fallback
            sb_input = self.config.get("scoreboard", {}).get("input", "")
            selected_input = sb_input
        elif input_combo is not None:
            # NEW STYLE CALL (from nameplate)
            selected_input = input_combo.get().strip()
        else:
            # Fallback to scoreboard
            selected_input = self.config.get("scoreboard", {}).get("input", "")
        
        # Get available fields for this input
        if is_image:
            available = self.available_image_fields.get(selected_input, [])
        else:
            available = self.available_text_fields.get(selected_input, [])
        
        # Combo box with available fields
        values = ["NONE"] + available if available else ["NONE"]
        combo = ttk.Combobox(parent, width=30, values=values)
        
        if current_value:
            combo.set(current_value)
        elif available:
            combo.set(available[0])
        else:
            combo.set("NONE")
        
        combo.grid(row=row, column=1, sticky=tk.W, padx=10, pady=3)
        
        # Only bind update handler for NEW style (with input_combo)
        if input_combo is not None:
            # Update fields when input changes
            def on_input_change(*args):
                new_input = input_combo.get().strip()
                if is_image:
                    new_fields = self.available_image_fields.get(new_input, [])
                else:
                    new_fields = self.available_text_fields.get(new_input, [])
                
                combo['values'] = ["NONE"] + new_fields if new_fields else ["NONE"]
                if new_fields:
                    combo.set(new_fields[0])
                else:
                    combo.set("NONE")
            
            # Bind to input combo changes
            input_combo.bind('<<ComboboxSelected>>', on_input_change)
        
        return combo

    # ========================================
    # Actions
    # ========================================
    # ========================================
    # TAB 7: Bilder (Image Mapping)
    # ========================================
    
    def _build_images_tab(self, notebook):
        """Build image mapping tab with Treeview table"""
        tab = ttk.Frame(notebook)
        notebook.add(tab, text="Bilder")
        
        # Scrollable frame
        canvas = tk.Canvas(tab, bg="#ecf0f1")
        scrollbar = ttk.Scrollbar(tab, orient="vertical", command=canvas.yview)
        content = tk.Frame(canvas, bg="#ecf0f1")
        
        content.bind(
            "<Configure>",
            lambda e: canvas.configure(scrollregion=canvas.bbox("all"))
        )
        
        canvas.create_window((0, 0), window=content, anchor="nw")
        canvas.configure(yscrollcommand=scrollbar.set)
        
        canvas.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        
        # Header
        tk.Label(
            content,
            text="BILDMAPPNING",
            font=("Segoe UI", 14, "bold"),
            bg="#2c3e50",
            fg="white",
            pady=10
        ).pack(fill=tk.X)
        
        # Info text
        info_frame = tk.Frame(content, bg="#e3f2fd", pady=10, padx=10)
        info_frame.pack(fill=tk.X, padx=10, pady=10)
        
        tk.Label(
            info_frame,
            text=("Här mappar du vilka bilder appen ska använda från vMix eller lokalt.\n"
                  "Dubbelklicka på INPUT eller FÄLT för att ändra.\n"
                  "Klicka [SÖK] för att välja lokal fil."),
            font=("Segoe UI", 9),
            bg="#e3f2fd",
            fg="#1565c0",
            justify=tk.LEFT
        ).pack()
        
        # Treeview frame
        tree_frame = tk.Frame(content, bg="#ecf0f1")
        tree_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        # Treeview with 5 columns
        columns = ('type', 'input', 'field', 'preview', 'local')
        
        self.images_tree = ttk.Treeview(
            tree_frame,
            columns=columns,
            show='headings',
            height=8,
            selectmode='browse'
        )
        
        # Column headers
        self.images_tree.heading('type', text='BILDTYP')
        self.images_tree.heading('input', text='INPUT')
        self.images_tree.heading('field', text='FÄLT')
        self.images_tree.heading('preview', text='PREVIEW')
        self.images_tree.heading('local', text='LOKAL')
        
        # Column widths
        self.images_tree.column('type', width=200, anchor='w')
        self.images_tree.column('input', width=180, anchor='w')
        self.images_tree.column('field', width=180, anchor='w')
        self.images_tree.column('preview', width=80, anchor='center')
        self.images_tree.column('local', width=80, anchor='center')
        
        # Scrollbar for tree
        tree_scroll = ttk.Scrollbar(tree_frame, orient="vertical", command=self.images_tree.yview)
        self.images_tree.configure(yscrollcommand=tree_scroll.set)
        
        self.images_tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        tree_scroll.pack(side=tk.RIGHT, fill=tk.Y)
        
        # Bind double-click
        self.images_tree.bind('<Double-Button-1>', self._on_image_double_click)
        
        # Load image mappings
        self._load_image_mappings()
        
        # Buttons
        btn_frame = tk.Frame(content, bg="#ecf0f1")
        btn_frame.pack(fill=tk.X, padx=10, pady=10)
        
        tk.Button(
            btn_frame,
            text="➕ Lägg till bildtyp",
            font=("Segoe UI", 9),
            command=self._add_image_mapping,
            bg="#4CAF50",
            fg="white"
        ).pack(side=tk.LEFT, padx=5)
        
        tk.Button(
            btn_frame,
            text="➖ Ta bort vald",
            font=("Segoe UI", 9),
            command=self._remove_image_mapping,
            bg="#f44336",
            fg="white"
        ).pack(side=tk.LEFT, padx=5)
    
    def _load_image_mappings(self):
        """Load image mappings from config into tree"""
        # Clear existing
        for item in self.images_tree.get_children():
            self.images_tree.delete(item)
        
        # Get image_mapping from config
        image_map = self.config.get("image_mapping", {})
        
        # Default mappings if none exist
        if not image_map:
            image_map = {
                "logo_home": {
                    "type": "Logo Hemmalag",
                    "source": "vmix",
                    "input": "SCOREBOARD UPPE",
                    "field": "HomeLogo.Source",
                    "local_path": None
                },
                "logo_away": {
                    "type": "Logo Bortalag",
                    "source": "vmix",
                    "input": "SCOREBOARD UPPE",
                    "field": "AwayLogo.Source",
                    "local_path": None
                }
            }
        
        # Populate tree
        for key, mapping in image_map.items():
            source = mapping.get("source", "vmix")
            input_name = mapping.get("input", "-") if source == "vmix" else "-"
            field_name = mapping.get("field", "-") if source == "vmix" else "-"
            local_file = mapping.get("local_path", "")
            
            preview = "🖼️" if source == "vmix" or local_file else "-"
            local_display = "[Lokal]" if local_file else "[SÖK]"
            
            self.images_tree.insert('', tk.END, iid=key, values=(
                mapping.get("type", key),
                input_name,
                field_name,
                preview,
                local_display
            ))
    
    def _on_image_double_click(self, event):
        """Handle double-click on tree item"""
        # Get clicked region
        region = self.images_tree.identify_region(event.x, event.y)
        if region != "cell":
            return
        
        # Get clicked column
        column = self.images_tree.identify_column(event.x)
        item = self.images_tree.identify_row(event.y)
        
        if not item:
            return
        
        # Column #2 = INPUT, #3 = FÄLT
        if column == '#2':  # INPUT
            self._edit_image_input(item)
        elif column == '#3':  # FÄLT
            self._edit_image_field(item)
        elif column == '#5':  # LOKAL
            self._browse_local_image(item)
    
    def _edit_image_input(self, item):
        """Edit input for image mapping"""
        from gui.dialogs import SimpleInputDialog
        
        current_values = self.images_tree.item(item)['values']
        current_input = current_values[1] if current_values[1] != '-' else ''
        
        # Show dropdown with available inputs
        dialog = SimpleInputDialog(
            self,
            "Välj Input",
            "Input:",
            current_input,
            self.available_inputs
        )
        self.wait_window(dialog)
        
        if dialog.result:
            # Update tree
            values = list(current_values)
            values[1] = dialog.result
            self.images_tree.item(item, values=values)
    
    def _edit_image_field(self, item):
        """Edit field for image mapping"""
        from gui.dialogs import SimpleInputDialog
        
        current_values = self.images_tree.item(item)['values']
        current_field = current_values[2] if current_values[2] != '-' else ''
        current_input = current_values[1]
        
        # Get available fields for this input
        available_fields = self.available_image_fields.get(current_input, [])
        
        if not available_fields:
            messagebox.showwarning(
                "Inga fält",
                f"Inga bildfält hittades för input '{current_input}'"
            )
            return
        
        # Show dropdown with available fields
        dialog = SimpleInputDialog(
            self,
            "Välj Fält",
            "Fält:",
            current_field,
            available_fields
        )
        self.wait_window(dialog)
        
        if dialog.result:
            # Update tree
            values = list(current_values)
            values[2] = dialog.result
            self.images_tree.item(item, values=values)
    
    def _browse_local_image(self, item):
        """Browse for local image file"""
        from tkinter import filedialog
        
        filepath = filedialog.askopenfilename(
            title="Välj bild",
            filetypes=[
                ("Bildfiler", "*.png *.jpg *.jpeg *.gif"),
                ("Alla filer", "*.*")
            ]
        )
        
        if filepath:
            # Store FULL filepath internally but show only filename
            filename = Path(filepath).name
            
            # Update tree display
            current_values = list(self.images_tree.item(item)['values'])
            current_values[4] = f"[{filename}]"
            
            # Clear vMix source when local file is selected
            current_values[1] = "-"
            current_values[2] = "-"
            
            self.images_tree.item(item, values=current_values)
            
            # Store full path in item tags for later retrieval
            self.images_tree.item(item, tags=(filepath,))
    
    def _add_image_mapping(self):
        """Add new image mapping"""
        # Simple dialog for image type name
        from gui.dialogs import SimpleInputDialog
        
        dialog = SimpleInputDialog(
            self,
            "Lägg till bildtyp",
            "Bildtyp (t.ex. 'Periodvila BG'):",
            ""
        )
        self.wait_window(dialog)
        
        if dialog.result:
            # Create unique key
            key = dialog.result.lower().replace(" ", "_")
            
            # Add to tree
            self.images_tree.insert('', tk.END, iid=key, values=(
                dialog.result,
                "-",
                "-",
                "-",
                "[SÖK]"
            ))
    
    def _remove_image_mapping(self):
        """Remove selected image mapping"""
        selection = self.images_tree.selection()
        if not selection:
            messagebox.showwarning("Ingen vald", "Välj en bildtyp att ta bort")
            return
        
        if messagebox.askyesno("Bekräfta", "Ta bort vald bildtyp?"):
            self.images_tree.delete(selection[0])
    
    # ========================================
    # Utilities
    # ========================================
    
    def _test_connection(self):
        """Test vMix connection"""
        from core.vmix_client import VMixClient
        
        host = self.vmix_host.get().strip()
        try:
            port = int(self.vmix_port.get().strip())
        except ValueError:
            messagebox.showerror("Fel", "Port måste vara ett nummer")
            return
        
        password = self.vmix_password.get().strip() or None
        
        try:
            client = VMixClient(host, port, password)
            _ = client.get_status_xml()
            messagebox.showinfo("Lyckades", f"Ansluten till vMix på {host}:{port}")
            
            # Refresh inputs
            self.vmix_client = client
            self._fetch_vmix_data()
            
        except Exception as e:
            messagebox.showerror("Anslutningsfel", f"Kunde inte ansluta:\n{e}")

    def _on_save(self):
        """Save configuration"""
        try:
            # Links (NEW for v4.3)
            if hasattr(self, 'link_vars'):
                for key, var in self.link_vars.items():
                    self.config[key] = var.get().strip()
            
            # vMix
            self.config["vmix"]["host"] = self.vmix_host.get().strip()
            self.config["vmix"]["port"] = int(self.vmix_port.get().strip())
            password = self.vmix_password.get().strip()
            self.config["vmix"]["password"] = password if password else None
            
            # Scoreboard
            self.config["scoreboard"]["input"] = self.sb_input.get().strip()
            self.config["scoreboard"]["overlay_channel"] = int(self.sb_overlay_channel.get())
            
            for key, combo in self.sb_fields.items():
                self.config["scoreboard"][key] = combo.get().strip()
            
            # Scoreboard NERE (NEW)
            if "scoreboard_nere" not in self.config:
                self.config["scoreboard_nere"] = {}
            
            self.config["scoreboard_nere"]["input"] = self.sb_nere_input.get().strip()
            self.config["scoreboard_nere"]["overlay_channel"] = int(self.sb_nere_overlay.get())
            
            for key, combo in self.sb_nere_fields.items():
                self.config["scoreboard_nere"][key] = combo.get().strip()
            
            # Penalties
            if "penalties" not in self.config["scoreboard"]:
                self.config["scoreboard"]["penalties"] = {}
            
            for slot, fields in self.penalty_fields.items():
                self.config["scoreboard"]["penalties"][slot] = {
                    "time_field": fields["time_field"].get().strip(),
                    "number_field": fields["number_field"].get().strip(),
                    "time_bg_field": fields["time_bg_field"].get().strip(),
                    "number_bg_field": fields["number_bg_field"].get().strip()
                }
            
            # Goal graphics
            self.config["goal_graphic"]["input"] = self.goal_input.get().strip()
            self.config["goal_graphic"]["overlay_channel"] = int(self.goal_overlay.get())
            self.config["goal_graphic"]["duration_ms"] = int(self.goal_duration.get().strip())
            
            self.config["after_goal_graphic"]["input"] = self.after_goal_input.get().strip()
            self.config["after_goal_graphic"]["overlay_channel"] = int(self.after_goal_overlay.get())
            self.config["after_goal_graphic"]["duration_ms"] = int(self.after_goal_duration.get().strip())
            self.config["after_goal_graphic"]["pause_before_ms"] = int(self.after_goal_pause.get().strip())
            
            # After Goal field mappings
            self.config["after_goal_graphic"]["number_field"] = self.after_goal_number_field.get().strip()
            self.config["after_goal_graphic"]["name_field"] = self.after_goal_name_field.get().strip()
            self.config["after_goal_graphic"]["team_field"] = self.after_goal_team_field.get().strip()
            self.config["after_goal_graphic"]["logo_field"] = self.after_goal_logo_field.get().strip()
            
            # Lineup
            self.config["lineup"]["home_input"] = self.lineup_home.get().strip()
            self.config["lineup"]["away_input"] = self.lineup_away.get().strip()
            
            # Nameplate - SPELARE
            if "nameplate" not in self.config:
                self.config["nameplate"] = {}
            
            self.config["nameplate"]["player_input"] = self.nameplate_player_input.get().strip()
            self.config["nameplate"]["staff_input"] = self.nameplate_staff_input.get().strip()
            self.config["nameplate"]["overlay_channel"] = int(self.nameplate_overlay_channel.get().strip())
            
            # Player fields
            self.config["nameplate"]["number_field"] = self.nameplate_number_field.get().strip()
            self.config["nameplate"]["name_field"] = self.nameplate_name_field.get().strip()
            self.config["nameplate"]["team_field"] = self.nameplate_team_field.get().strip()
            self.config["nameplate"]["logo_field"] = self.nameplate_logo_field.get().strip()
            
            # Staff fields (separate or use same?)
            self.config["nameplate"]["staff_name_field"] = self.nameplate_staff_name_field.get().strip()
            self.config["nameplate"]["staff_role_field"] = self.nameplate_staff_role_field.get().strip()
            self.config["nameplate"]["staff_team_field"] = self.nameplate_staff_team_field.get().strip()
            self.config["nameplate"]["staff_logo_field"] = self.nameplate_staff_logo_field.get().strip()
            
            # Image mappings (optional - only if images tab exists)
            if hasattr(self, 'images_tree') and "image_mapping" not in self.config:
                self.config["image_mapping"] = {}
            
            # Clear and rebuild from tree (only if images tree exists)
            if hasattr(self, 'images_tree'):
                self.config["image_mapping"] = {}
                
                for item in self.images_tree.get_children():
                    key = item  # item ID is the key
                    values = self.images_tree.item(item)['values']
                    tags = self.images_tree.item(item)['tags']
                    
                    # Parse values
                    image_type = values[0]
                    input_name = values[1] if values[1] != '-' else None
                    field_name = values[2] if values[2] != '-' else None
                    local_display = values[4]
                    
                    # Determine source and get full path from tags
                    if local_display and local_display.startswith('[') and local_display != '[SÖK]':
                        source = "local"
                        # Try to get full path from tags, otherwise use display name
                        local_path = tags[0] if tags else local_display.strip('[]')
                    else:
                        source = "vmix"
                        local_path = None
                    
                    self.config["image_mapping"][key] = {
                        "type": image_type,
                        "source": source,
                        "input": input_name,
                        "field": field_name,
                        "local_path": local_path
                    }
            
            # Save to file
            with open("config.json", "w", encoding="utf-8") as f:
                json.dump(self.config, f, indent=2, ensure_ascii=False)
            
            self.result = self.config
            messagebox.showinfo("Sparat", "Inställningar sparade!\n\nStarta om applikationen för att ändringarna ska träda i kraft.")
            self.destroy()
            
        except Exception as e:
            messagebox.showerror("Fel", f"Kunde inte spara:\n{e}")
    
    # ========================================
    # TAB 8: Data Export
    # ========================================
    def _build_export_tab(self, notebook):
        """JSON File Export - SIMPLIFIED"""
        frame = ttk.Frame(notebook)
        notebook.add(frame, text="Export")
        
        content = tk.Frame(frame, bg="#ecf0f1")
        content.pack(fill=tk.BOTH, expand=True, padx=20, pady=20)
        
        # Header
        tk.Label(
            content,
            text="JSON EXPORT",
            font=("Segoe UI", 14, "bold"),
            bg="#ecf0f1",
            fg="#2c3e50"
        ).pack(pady=(0, 10))
        
        # Info
        tk.Label(
            content,
            text="Exportera lineup-data till JSON-filer som vMix kan läsa lokalt.\n"
                 "Detta gör data stabil även om API eller nätverk svajar.",
            font=("Segoe UI", 9),
            bg="#ecf0f1",
            fg="#666",
            justify=tk.LEFT
        ).pack(pady=5, padx=10, anchor="w")
        
        # Export folder setting
        folder_frame = tk.Frame(content, bg="#ecf0f1")
        folder_frame.pack(fill=tk.X, pady=20)
        
        tk.Label(
            folder_frame,
            text="Exportmapp:",
            font=("Segoe UI", 10, "bold"),
            bg="#ecf0f1"
        ).pack(side=tk.LEFT, padx=5)
        
        self.export_folder_var = tk.StringVar(
            value=self.config.get("export_folder", "C:\\vMix\\")
        )
        
        tk.Entry(
            folder_frame,
            textvariable=self.export_folder_var,
            font=("Segoe UI", 10),
            width=40
        ).pack(side=tk.LEFT, padx=5)
        
        tk.Button(
            folder_frame,
            text="Bläddra...",
            font=("Segoe UI", 9),
            command=self._browse_export_folder,
            bg="#95a5a6",
            fg="white"
        ).pack(side=tk.LEFT, padx=5)
        
        # File list
        files_frame = tk.LabelFrame(
            content,
            text="Filer som exporteras:",
            font=("Segoe UI", 10, "bold"),
            bg="#ecf0f1"
        )
        files_frame.pack(fill=tk.BOTH, expand=True, pady=10, padx=10)
        
        files = [
            ("lineup.json", "Komplett laguppställning (spelare + ledare + logos)"),
            ("scoreboard.json", "Scoreboard data (logos + lagnamn från SLH)"),
            ("match.json", "Matchinformation (basic team info)")
        ]
        
        for filename, desc in files:
            file_row = tk.Frame(files_frame, bg="white", relief=tk.RIDGE, bd=1)
            file_row.pack(fill=tk.X, padx=10, pady=5)
            
            tk.Label(
                file_row,
                text=f"✓ {filename}",
                font=("Segoe UI", 10, "bold"),
                bg="white",
                fg="#27ae60",
                width=20,
                anchor="w"
            ).pack(side=tk.LEFT, padx=10, pady=5)
            
            tk.Label(
                file_row,
                text=desc,
                font=("Segoe UI", 9),
                bg="white",
                fg="#555"
            ).pack(side=tk.LEFT, padx=10)
        
        # Export button
        tk.Button(
            content,
            text="✓ EXPORTERA ALLA FILER",
            font=("Segoe UI", 12, "bold"),
            bg="#2196F3",
            fg="white",
            command=self._export_all_json_now,
            padx=30,
            pady=15
        ).pack(pady=20)
    
    def _browse_export_folder(self):
        """Browse for export folder"""
        from tkinter import filedialog
        
        folder = filedialog.askdirectory(
            title="Välj exportmapp",
            initialdir=self.export_folder_var.get()
        )
        
        if folder:
            self.export_folder_var.set(folder)
            self.config["export_folder"] = folder
    
    def _export_all_json_now(self):
        """Export all JSON files"""
        # Check if parent has lineup_state
        if not hasattr(self.parent, 'lineup_state'):
            messagebox.showerror("Fel", "Lineup state saknas")
            return
        
        lineup_state = self.parent.lineup_state
        
        if not lineup_state.has_data():
            messagebox.showwarning(
                "Ingen data",
                "Ingen lineup inläst att exportera.\n\n"
                "Ladda först en lineup från API, SweHockey eller vMix."
            )
            return
        
        # Check if parent has json_exporter
        if not hasattr(self.parent, 'json_exporter') or not self.parent.json_exporter:
            messagebox.showerror(
                "Fel",
                "JSON exporter inte initialiserad.\n\n"
                "Ladda lineup först."
            )
            return
        
        json_exporter = self.parent.json_exporter
        export_folder = self.export_folder_var.get()
        
        if not export_folder:
            messagebox.showwarning("Ingen mapp", "Välj exportmapp först")
            return
        
        # Export all files
        try:
            results = []
            
            # Export lineup
            msg = json_exporter.export_lineup_json(
                f"{export_folder}/lineup.json"
            )
            results.append(msg)
            
            # Export scoreboard
            msg = json_exporter.export_scoreboard_json(
                f"{export_folder}/scoreboard.json"
            )
            results.append(msg)
            
            # Export match
            msg = json_exporter.export_match_json(
                f"{export_folder}/match.json"
            )
            results.append(msg)
            
            # Save export folder to config
            self.config["export_folder"] = export_folder
            
            # Show results
            msg_text = "Export klar!\n\n" + "\n".join(results)
            msg_text += f"\n\nFiler sparade i: {export_folder}"
            
            messagebox.showinfo("Export klar", msg_text)
            
        except Exception as e:
            import traceback
            traceback.print_exc()
            messagebox.showerror("Export misslyckades", f"Fel vid export:\n\n{e}")

    
    # ========================================
    # TAB: Länkar (NEW for v4.3)
    # ========================================
    def _build_links_tab(self, notebook):
        """Links and folder settings"""
        frame = ttk.Frame(notebook)
        notebook.add(frame, text="Länkar")
        
        # Create canvas + scrollbar for scrolling
        canvas = tk.Canvas(frame, bg="#ecf0f1")
        scrollbar = ttk.Scrollbar(frame, orient="vertical", command=canvas.yview)
        scrollable_frame = tk.Frame(canvas, bg="#ecf0f1")
        
        scrollable_frame.bind(
            "<Configure>",
            lambda e: canvas.configure(scrollregion=canvas.bbox("all"))
        )
        
        canvas.create_window((0, 0), window=scrollable_frame, anchor="nw")
        canvas.configure(yscrollcommand=scrollbar.set)
        
        canvas.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")
        
        content = tk.Frame(scrollable_frame, bg="#ecf0f1")
        content.pack(fill=tk.BOTH, expand=True, padx=20, pady=20)
        
        # Header
        tk.Label(
            content,
            text="LÄNKAR OCH MAPPAR",
            font=("Segoe UI", 14, "bold"),
            bg="#ecf0f1",
            fg="#2c3e50"
        ).pack(pady=(0, 10))
        
        # Info
        tk.Label(
            content,
            text="Konfigurera URLs och lokala mappar för import/export.",
            font=("Segoe UI", 9),
            bg="#ecf0f1",
            fg="#666"
        ).pack(pady=5)
        
        # API URLs Section
        api_frame = tk.LabelFrame(
            content,
            text="API URLs",
            font=("Segoe UI", 10, "bold"),
            bg="#ecf0f1"
        )
        api_frame.pack(fill=tk.X, pady=10, padx=10)
        
        self._add_setting_row(
            api_frame,
            "Hockeyettan API:",
            "api_base_url",
            "https://vmix-new.hockeyettan.se/api"
        )
        
        self._add_setting_row(
            api_frame,
            "SweHockey URL:",
            "swehockey_base_url",
            "https://stats.swehockey.se"
        )
        
        # Logo Folders Section
        logo_frame = tk.LabelFrame(
            content,
            text="Logo Mappar",
            font=("Segoe UI", 10, "bold"),
            bg="#ecf0f1"
        )
        logo_frame.pack(fill=tk.X, pady=10, padx=10)
        
        self._add_folder_row(
            logo_frame,
            "Logo Pregame (stora):",
            "logo_pregame_folder",
            "C:\\H1_Grafikpaket\\LOGO Pregame\\"
        )
        
        self._add_folder_row(
            logo_frame,
            "Logo Teams (små):",
            "logo_teams_folder",
            "C:\\H1_Grafikpaket\\LOGO Teams\\"
        )
        
        self._add_folder_row(
            logo_frame,
            "Resources (plates etc):",
            "resources_folder",
            "C:\\H1_Grafikpaket\\TITLES\\RESOURCES\\"
        )
        
        # Export Folder Section
        export_frame = tk.LabelFrame(
            content,
            text="Export Mapp",
            font=("Segoe UI", 10, "bold"),
            bg="#ecf0f1"
        )
        export_frame.pack(fill=tk.X, pady=10, padx=10)
        
        self._add_folder_row(
            export_frame,
            "Export till:",
            "export_folder",
            "C:\\vMix\\"
        )
        
        # Import Folder Section
        import_frame = tk.LabelFrame(
            content,
            text="Import Mapp",
            font=("Segoe UI", 10, "bold"),
            bg="#ecf0f1"
        )
        import_frame.pack(fill=tk.X, pady=10, padx=10)
        
        self._add_folder_row(
            import_frame,
            "Import från:",
            "import_folder",
            "C:\\Data\\"
        )
    
    def _add_setting_row(self, parent, label_text, config_key, default_value):
        """Add a setting row with label and entry"""
        row = tk.Frame(parent, bg="#ecf0f1")
        row.pack(fill=tk.X, padx=10, pady=5)
        
        tk.Label(
            row,
            text=label_text,
            font=("Segoe UI", 9),
            bg="#ecf0f1",
            width=20,
            anchor="w"
        ).pack(side=tk.LEFT, padx=5)
        
        var = tk.StringVar(value=self.config.get(config_key, default_value))
        
        entry = tk.Entry(
            row,
            textvariable=var,
            font=("Segoe UI", 9),
            width=50
        )
        entry.pack(side=tk.LEFT, padx=5, fill=tk.X, expand=True)
        
        # Store variable for saving later
        if not hasattr(self, 'link_vars'):
            self.link_vars = {}
        self.link_vars[config_key] = var
    
    def _add_folder_row(self, parent, label_text, config_key, default_value):
        """Add a folder setting row with browse button"""
        row = tk.Frame(parent, bg="#ecf0f1")
        row.pack(fill=tk.X, padx=10, pady=5)
        
        tk.Label(
            row,
            text=label_text,
            font=("Segoe UI", 9),
            bg="#ecf0f1",
            width=20,
            anchor="w"
        ).pack(side=tk.LEFT, padx=5)
        
        var = tk.StringVar(value=self.config.get(config_key, default_value))
        
        entry = tk.Entry(
            row,
            textvariable=var,
            font=("Segoe UI", 9),
            width=40
        )
        entry.pack(side=tk.LEFT, padx=5, fill=tk.X, expand=True)
        
        def browse():
            from tkinter import filedialog
            folder = filedialog.askdirectory(
                title=f"Välj {label_text}",
                initialdir=var.get()
            )
            if folder:
                var.set(folder)
        
        tk.Button(
            row,
            text="Bläddra...",
            font=("Segoe UI", 8),
            command=browse,
            bg="#95a5a6",
            fg="white"
        ).pack(side=tk.LEFT, padx=5)
        
        # Store variable for saving later
        if not hasattr(self, 'link_vars'):
            self.link_vars = {}
        self.link_vars[config_key] = var
