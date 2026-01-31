"""
Team Importer Panel
Step 2: Import teams from API or files
"""

import tkinter as tk
from tkinter import ttk, messagebox, filedialog, simpledialog
from typing import List, Optional, Callable
import json

from core.data_manager import DataManager
from core.data_models import Season, Team
from core.api_parser import HockeyettanAPIParser


class TeamImporterPanel(tk.Frame):
    """Panel for importing teams"""
    
    def __init__(self, parent, data_manager: DataManager, 
                 current_sport: Optional[str] = None,
                 current_season: Optional[str] = None):
        super().__init__(parent, bg="#f5f5f5")
        
        self.data_manager = data_manager
        self.current_sport = current_sport
        self.current_season = current_season
        self.current_series = None
        
        self.teams = []
        
        self._build_ui()
        self._load_season_data()
    
    def set_season(self, sport: str, year: str):
        """Update current season"""
        self.current_sport = sport
        self.current_season = year
        self._load_season_data()
    
    def _load_season_data(self):
        """Load season and populate series selector"""
        if not self.current_sport or not self.current_season:
            return
        
        season = self.data_manager.get_season(self.current_sport, self.current_season)
        if not season:
            return
        
        # Populate series dropdown
        series_names = list(season.series.keys())
        self.series_combo['values'] = series_names
        
        if series_names:
            self.series_combo.set(series_names[0])
            self.current_series = series_names[0]
            self._load_teams()
    
    def _build_ui(self):
        """Build team importer UI"""
        # Top: Series selector and import button
        top_frame = tk.Frame(self, bg="#f5f5f5")
        top_frame.pack(fill=tk.X, pady=(0, 20))
        
        tk.Label(
            top_frame,
            text="Serie:",
            font=("Segoe UI", 11, "bold"),
            bg="#f5f5f5"
        ).pack(side=tk.LEFT, padx=(0, 10))
        
        self.series_combo = ttk.Combobox(
            top_frame,
            font=("Segoe UI", 11),
            state="readonly",
            width=20
        )
        self.series_combo.pack(side=tk.LEFT, padx=(0, 20))
        self.series_combo.bind('<<ComboboxSelected>>', self._on_series_change)
        
        tk.Button(
            top_frame,
            text="📥 Importera från API",
            font=("Segoe UI", 10, "bold"),
            command=self._import_from_api_file,
            bg="#3498db",
            fg="white",
            relief="flat",
            cursor="hand2",
            padx=15,
            pady=8
        ).pack(side=tk.LEFT, padx=5)
        
        tk.Button(
            top_frame,
            text="🌐 SweHockey",
            font=("Segoe UI", 10, "bold"),
            command=self._import_from_swehockey,
            bg="#e67e22",
            fg="white",
            relief="flat",
            cursor="hand2",
            padx=15,
            pady=8
        ).pack(side=tk.LEFT, padx=5)
        
        tk.Button(
            top_frame,
            text="+ Lägg till manuellt",
            font=("Segoe UI", 10),
            command=self._add_team_manual,
            bg="white",
            fg="#2c3e50",
            relief="solid",
            bd=1,
            cursor="hand2",
            padx=15,
            pady=8
        ).pack(side=tk.LEFT, padx=5)
        
        # Middle: Team table
        table_frame = tk.Frame(self, bg="white", relief="solid", bd=1)
        table_frame.pack(fill=tk.BOTH, expand=True)
        
        # Table header
        header = tk.Frame(table_frame, bg="#ecf0f1", height=35)
        header.pack(fill=tk.X)
        header.pack_propagate(False)
        
        columns = [
            ("Pos", 50),
            ("Lagnamn", 250),
            ("Kort", 80),
            ("Logo (liten)", 150),
            ("Logo (stor)", 150),
            ("Club ID", 80)
        ]
        
        for col_name, width in columns:
            label = tk.Label(
                header,
                text=col_name,
                font=("Segoe UI", 10, "bold"),
                bg="#ecf0f1",
                fg="#2c3e50",
                width=width // 8
            )
            label.pack(side=tk.LEFT, padx=5)
        
        # Scrollable table
        canvas = tk.Canvas(table_frame, bg="white")
        scrollbar = ttk.Scrollbar(table_frame, orient="vertical", command=canvas.yview)
        self.table_container = tk.Frame(canvas, bg="white")
        
        # Store canvas reference
        self.table_canvas = canvas
        
        self.table_container.bind(
            "<Configure>",
            lambda e: canvas.configure(scrollregion=canvas.bbox("all"))
        )
        
        canvas.create_window((0, 0), window=self.table_container, anchor="nw")
        canvas.configure(yscrollcommand=scrollbar.set)
        
        canvas.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        
        # Bottom: Save button
        bottom_frame = tk.Frame(self, bg="#f5f5f5")
        bottom_frame.pack(fill=tk.X, pady=(20, 0))
        
        tk.Label(
            bottom_frame,
            text=f"Antal lag: 0",
            font=("Segoe UI", 10),
            bg="#f5f5f5",
            fg="#7f8c8d"
        ).pack(side=tk.LEFT)
        
        self.count_label = bottom_frame.winfo_children()[0]
        
        tk.Button(
            bottom_frame,
            text="💾 SPARA LAG",
            font=("Segoe UI", 11, "bold"),
            command=self._save_teams,
            bg="#27ae60",
            fg="white",
            relief="flat",
            cursor="hand2",
            padx=30,
            pady=10
        ).pack(side=tk.RIGHT)
    
    def _on_series_change(self, event):
        """Handle series change"""
        self.current_series = self.series_combo.get()
        self._load_teams()
    
    def _load_teams(self):
        """Load teams for current series"""
        if not self.current_sport or not self.current_season or not self.current_series:
            return
        
        self.teams = self.data_manager.load_teams(
            self.current_sport,
            self.current_season,
            self.current_series
        )
        
        self._refresh_table()
    
    def _refresh_table(self):
        """Refresh team table"""
        # Clear existing rows
        for widget in self.table_container.winfo_children():
            widget.destroy()
        
        # Update count first
        if hasattr(self, 'count_label'):
            self.count_label.configure(text=f"Antal lag: {len(self.teams)}")
        
        # If no teams, show message
        if not self.teams:
            empty_label = tk.Label(
                self.table_container,
                text="Inga lag importerade ännu.\n\nKlicka på 'Importera från API' för att börja.",
                font=("Segoe UI", 11),
                bg="white",
                fg="#95a5a6",
                pady=50
            )
            empty_label.pack(fill=tk.BOTH, expand=True)
            return
        
        # Add rows
        for i, team in enumerate(self.teams):
            row = tk.Frame(self.table_container, bg="white" if i % 2 == 0 else "#f8f9fa", height=40)
            row.pack(fill=tk.X, pady=2, padx=5)
            row.pack_propagate(False)
            
            # Position
            tk.Label(
                row,
                text=str(team.position or i + 1),
                font=("Segoe UI", 10),
                bg=row['bg'],
                width=4
            ).pack(side=tk.LEFT, padx=5)
            
            # Name
            name_label = tk.Label(
                row,
                text=team.name[:35],  # Truncate if too long
                font=("Segoe UI", 10),
                bg=row['bg'],
                anchor="w"
            )
            name_label.pack(side=tk.LEFT, padx=5, fill=tk.X, expand=False)
            name_label.config(width=35)
            
            # Short name
            tk.Label(
                row,
                text=team.short_name,
                font=("Segoe UI", 10, "bold"),
                bg=row['bg'],
                fg="#3498db",
                width=8
            ).pack(side=tk.LEFT, padx=5)
            
            # Logo small (show shortname only)
            tk.Label(
                row,
                text=f"{team.short_name}.png" if team.short_name else "...",
                font=("Segoe UI", 9),
                bg=row['bg'],
                fg="#7f8c8d",
                width=15
            ).pack(side=tk.LEFT, padx=5)
            
            # Logo large (show shortname only)
            tk.Label(
                row,
                text=f"{team.short_name}.png" if team.short_name else "...",
                font=("Segoe UI", 9),
                bg=row['bg'],
                fg="#7f8c8d",
                width=15
            ).pack(side=tk.LEFT, padx=5)
            
            # Club ID (editable)
            club_id_entry = tk.Entry(
                row,
                font=("Segoe UI", 10),
                width=10,
                bg="white",
                relief="solid",
                bd=1
            )
            club_id_entry.insert(0, team.club_id or "")
            club_id_entry.pack(side=tk.LEFT, padx=5)
            
            # Store reference for saving
            club_id_entry.team_index = i
        
        # CRITICAL: Force update of canvas scroll region
        self.table_container.update_idletasks()
        
        print(f"✓ Displayed {len(self.teams)} teams in table")
    
    def _import_from_api_file(self):
        """Import from API JSON file"""
        # Open file dialog
        filepath = filedialog.askopenfilename(
            title="Välj API-fil (tabel JSON)",
            filetypes=[("JSON files", "*.json"), ("Text files", "*.txt"), ("All files", "*.*")]
        )
        
        if not filepath:
            return
        
        try:
            # Read file
            with open(filepath, 'r', encoding='utf-8') as f:
                json_data = f.read()
            
            # Parse
            parser = HockeyettanAPIParser()
            teams = parser.parse_tabel(json_data)
            
            if not teams:
                messagebox.showwarning("Inga lag", "Kunde inte hitta några lag i filen")
                return
            
            # Replace current teams
            self.teams = teams
            self._refresh_table()
            
            messagebox.showinfo(
                "Importerat!",
                f"Importerade {len(teams)} lag från API-data!\n\nGranska och fyll i Club ID om du vill."
            )
            
        except Exception as e:
            messagebox.showerror("Import misslyckades", f"Kunde inte läsa fil:\n\n{e}")
    
    def _import_from_swehockey(self):
        """Import from SweHockey scraping"""
        # Get series ID
        series_id = tk.simpledialog.askstring(
            "SweHockey Serie-ID",
            f"Ange serie-ID från SweHockey:\n\nExempel:\nNORRA: 18270\nSÖDRA: 18271\n\nHitta på: stats.swehockey.se"
        )
        
        if not series_id:
            return
        
        messagebox.showinfo(
            "SweHockey scraping",
            f"SweHockey scraping för serie {series_id} kommer i v5.2!\n\nAnvänd 'Importera från API' och välj TabellNorra.txt eller TabellSödra.txt"
        )
    
    def _add_team_manual(self):
        """Add team manually"""
        messagebox.showinfo("Manuell inläggning", "Kommer i nästa version")
    
    def _save_teams(self):
        """Save teams to data manager"""
        if not self.current_sport or not self.current_season or not self.current_series:
            messagebox.showwarning("Ingen serie vald", "Välj sport, säsong och serie först")
            return
        
        if not self.teams:
            messagebox.showwarning("Inga lag", "Lägg till lag först")
            return
        
        # Update club IDs from entry fields
        for widget in self.table_container.winfo_children():
            for child in widget.winfo_children():
                if isinstance(child, tk.Entry) and hasattr(child, 'team_index'):
                    idx = child.team_index
                    if idx < len(self.teams):
                        self.teams[idx].club_id = child.get().strip() or None
        
        # Save
        self.data_manager.save_teams(
            self.current_sport,
            self.current_season,
            self.current_series,
            self.teams
        )
        
        # Update season object with teams
        season = self.data_manager.get_season(self.current_sport, self.current_season)
        if season and self.current_series in season.series:
            season.series[self.current_series].teams = self.teams
            self.data_manager.save_season(season)
        
        messagebox.showinfo(
            "Sparat!",
            f"{len(self.teams)} lag sparade för {self.current_series}!\n\nGå vidare till nästa steg."
        )
