# gui/lineup_editor.py
"""
Editable Lineup Tab for v4.3
Treeview-based editor with import/export per team
"""

import tkinter as tk
from tkinter import ttk, messagebox, filedialog
from typing import Dict, List, Optional


class LineupEditor(tk.Frame):
    """
    Editable lineup editor with import/export
    """
    
    def __init__(self, parent, config, data_manager=None, vmix_client=None):
        super().__init__(parent, bg="#ecf0f1")
        
        self.config = config
        self.data_manager = data_manager
        self.vmix_client = vmix_client
        
        # Try to get main window reference for lineup_state sync
        self.main_window = None
        try:
            # Navigate up to find MainWindowMobile
            widget = parent
            while widget:
                if hasattr(widget, 'lineup_state'):
                    self.main_window = widget
                    break
                widget = widget.master if hasattr(widget, 'master') else None
        except:
            pass
        
        self.home_players = []
        self.away_players = []
        
        self.home_logo_pregame = tk.StringVar()
        self.home_logo_teams = tk.StringVar()
        self.away_logo_pregame = tk.StringVar()
        self.away_logo_teams = tk.StringVar()
        
        self.home_team_name = tk.StringVar(value="")
        self.away_team_name = tk.StringVar(value="")
        self.home_team_short = tk.StringVar(value="")
        self.away_team_short = tk.StringVar(value="")
        
        self._build_ui()
    
    def _build_ui(self):
        """Build lineup editor UI"""
        # Header
        header = tk.Frame(self, bg="#2c3e50", height=60)
        header.pack(fill=tk.X)
        header.pack_propagate(False)
        
        tk.Label(
            header,
            text="LINEUP EDITOR",
            font=("Segoe UI", 16, "bold"),
            bg="#2c3e50",
            fg="white"
        ).pack(side=tk.LEFT, padx=20, pady=15)
        
        # Main content with two columns
        content = tk.Frame(self, bg="#ecf0f1")
        content.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        # Left: Home team
        left = tk.Frame(content, bg="#ecf0f1")
        left.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=5)
        
        self._build_team_section(left, "HEMMALAG", is_home=True)
        
        # Right: Away team
        right = tk.Frame(content, bg="#ecf0f1")
        right.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=5)
        
        self._build_team_section(right, "BORTALAG", is_home=False)
    
    def _build_team_section(self, parent, title, is_home=True):
        """Build one team section (home or away)"""
        # Team header
        header_frame = tk.LabelFrame(
            parent,
            text=title,
            font=("Segoe UI", 12, "bold"),
            bg="#ecf0f1"
        )
        header_frame.pack(fill=tk.X, pady=(0, 10))
        
        # Team name
        name_row = tk.Frame(header_frame, bg="white")
        name_row.pack(fill=tk.X, padx=10, pady=5)
        
        tk.Label(
            name_row,
            text="Lagnamn:",
            font=("Segoe UI", 9, "bold"),
            bg="white",
            width=12,
            anchor="w"
        ).pack(side=tk.LEFT, padx=5)
        
        team_var = self.home_team_name if is_home else self.away_team_name
        
        tk.Entry(
            name_row,
            textvariable=team_var,
            font=("Segoe UI", 10),
            width=25
        ).pack(side=tk.LEFT, padx=5, fill=tk.X, expand=True)
        
        # Team short name (NEW)
        short_row = tk.Frame(header_frame, bg="white")
        short_row.pack(fill=tk.X, padx=10, pady=5)
        
        tk.Label(
            short_row,
            text="Kort namn:",
            font=("Segoe UI", 9),
            bg="white",
            width=12,
            anchor="w"
        ).pack(side=tk.LEFT, padx=5)
        
        short_var = self.home_team_short if is_home else self.away_team_short
        
        tk.Entry(
            short_row,
            textvariable=short_var,
            font=("Segoe UI", 10),
            width=25
        ).pack(side=tk.LEFT, padx=5, fill=tk.X, expand=True)
        
        # Logo Pregame
        logo1_row = tk.Frame(header_frame, bg="white")
        logo1_row.pack(fill=tk.X, padx=10, pady=5)
        
        tk.Label(
            logo1_row,
            text="Logo (stor):",
            font=("Segoe UI", 9),
            bg="white",
            width=12,
            anchor="w"
        ).pack(side=tk.LEFT, padx=5)
        
        logo_var1 = self.home_logo_pregame if is_home else self.away_logo_pregame
        
        tk.Entry(
            logo1_row,
            textvariable=logo_var1,
            font=("Segoe UI", 8),
            width=20
        ).pack(side=tk.LEFT, padx=5, fill=tk.X, expand=True)
        
        tk.Button(
            logo1_row,
            text="...",
            font=("Segoe UI", 8),
            command=lambda: self._browse_logo(logo_var1, "pregame"),
            width=3
        ).pack(side=tk.LEFT, padx=2)
        
        # Logo Teams
        logo2_row = tk.Frame(header_frame, bg="white")
        logo2_row.pack(fill=tk.X, padx=10, pady=5)
        
        tk.Label(
            logo2_row,
            text="Logo (liten):",
            font=("Segoe UI", 9),
            bg="white",
            width=12,
            anchor="w"
        ).pack(side=tk.LEFT, padx=5)
        
        logo_var2 = self.home_logo_teams if is_home else self.away_logo_teams
        
        tk.Entry(
            logo2_row,
            textvariable=logo_var2,
            font=("Segoe UI", 8),
            width=20
        ).pack(side=tk.LEFT, padx=5, fill=tk.X, expand=True)
        
        tk.Button(
            logo2_row,
            text="...",
            font=("Segoe UI", 8),
            command=lambda: self._browse_logo(logo_var2, "teams"),
            width=3
        ).pack(side=tk.LEFT, padx=2)
        
        # Players Treeview
        tree_frame = tk.Frame(parent, bg="#ecf0f1")
        tree_frame.pack(fill=tk.BOTH, expand=True, pady=5)
        
        tk.Label(
            tree_frame,
            text="SPELARE:",
            font=("Segoe UI", 10, "bold"),
            bg="#ecf0f1"
        ).pack(anchor="w", pady=(0, 5))
        
        # Create treeview
        columns = ('nr', 'namn', 'pos', 'kategori')
        tree = ttk.Treeview(
            tree_frame,
            columns=columns,
            show='headings',
            height=15
        )
        
        tree.heading('nr', text='NR')
        tree.heading('namn', text='NAMN')
        tree.heading('pos', text='POS')
        tree.heading('kategori', text='KATEGORI')
        
        tree.column('nr', width=40, anchor='center')
        tree.column('namn', width=150, anchor='w')
        tree.column('pos', width=40, anchor='center')
        tree.column('kategori', width=60, anchor='center')
        
        # Scrollbar
        scrollbar = ttk.Scrollbar(tree_frame, orient='vertical', command=tree.yview)
        tree.configure(yscrollcommand=scrollbar.set)
        
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        
        # Bind double-click for editing
        tree.bind('<Double-Button-1>', lambda e: self._edit_cell(e, tree, is_home))
        
        # Store tree reference
        if is_home:
            self.home_tree = tree
        else:
            self.away_tree = tree
        
        # Buttons
        btn_frame = tk.Frame(parent, bg="#ecf0f1")
        btn_frame.pack(fill=tk.X, pady=10)
        
        tk.Button(
            btn_frame,
            text="Importera...",
            font=("Segoe UI", 9),
            command=lambda: self._import_team(is_home),
            bg="#3498db",
            fg="white",
            width=12
        ).pack(side=tk.LEFT, padx=5)
        
        tk.Button(
            btn_frame,
            text="+ Lägg till",
            font=("Segoe UI", 9),
            command=lambda: self._add_player(is_home),
            bg="#2ecc71",
            fg="white",
            width=10
        ).pack(side=tk.LEFT, padx=5)
        
        tk.Button(
            btn_frame,
            text="− Ta bort",
            font=("Segoe UI", 9),
            command=lambda: self._remove_player(is_home),
            bg="#e74c3c",
            fg="white",
            width=10
        ).pack(side=tk.LEFT, padx=5)
        
        # Export button (only show once for home team, exports both)
        if is_home:
            tk.Button(
                btn_frame,
                text="✓ Exportera",
                font=("Segoe UI", 9, "bold"),
                command=self._export_lineup,
                bg="#f39c12",
                fg="white",
                width=12
            ).pack(side=tk.RIGHT, padx=5)
    
    def _browse_logo(self, logo_var, logo_type):
        """Browse for logo file"""
        # Get initial dir from config
        if logo_type == "pregame":
            initial_dir = self.config.get("logo_pregame_folder", "C:\\")
        else:
            initial_dir = self.config.get("logo_teams_folder", "C:\\")
        
        filename = filedialog.askopenfilename(
            title=f"Välj logo ({logo_type})",
            initialdir=initial_dir,
            filetypes=[("PNG files", "*.png"), ("All files", "*.*")]
        )
        
        if filename:
            logo_var.set(filename)
    
    def _edit_cell(self, event, tree, is_home):
        """Edit cell on double-click"""
        region = tree.identify_region(event.x, event.y)
        if region != "cell":
            return
        
        column = tree.identify_column(event.x)
        item = tree.identify_row(event.y)
        
        if not item:
            return
        
        # Get column index (0-based)
        col_idx = int(column.replace('#', '')) - 1
        col_name = ('nr', 'namn', 'pos', 'kategori')[col_idx]
        
        # Get current value
        values = tree.item(item, 'values')
        current_value = values[col_idx]
        
        # Create edit dialog
        dialog = tk.Toplevel(self)
        dialog.title(f"Redigera {col_name.upper()}")
        dialog.geometry("400x150")
        dialog.transient(self)
        dialog.grab_set()
        
        tk.Label(
            dialog,
            text=f"Redigera {col_name.upper()}:",
            font=("Segoe UI", 10, "bold")
        ).pack(pady=10)
        
        if col_name == 'kategori':
            # Dropdown for kategori
            var = tk.StringVar(value=current_value)
            
            categories = [
                'GK1', 'GK2',
                'LD1', 'LD2', 'LD3', 'LD4', 'LD5',
                'RD1', 'RD2', 'RD3', 'RD4', 'RD5',
                'LW1', 'LW2', 'LW3', 'LW4', 'LW5',
                'C1', 'C2', 'C3', 'C4', 'C5',
                'RW1', 'RW2', 'RW3', 'RW4', 'RW5',
                'XD1', 'XD2', 'XD3', 'XD4', 'XD5'
            ]
            
            combo = ttk.Combobox(
                dialog,
                textvariable=var,
                values=categories,
                font=("Segoe UI", 10),
                width=20
            )
            combo.pack(pady=10)
            combo.focus()
        elif col_name == 'pos':
            # Dropdown for position
            var = tk.StringVar(value=current_value)
            
            combo = ttk.Combobox(
                dialog,
                textvariable=var,
                values=['GK', 'D', 'F'],
                font=("Segoe UI", 10),
                width=20
            )
            combo.pack(pady=10)
            combo.focus()
        else:
            # Text entry for nr/namn
            var = tk.StringVar(value=current_value)
            
            entry = tk.Entry(
                dialog,
                textvariable=var,
                font=("Segoe UI", 10),
                width=30
            )
            entry.pack(pady=10)
            entry.focus()
            entry.select_range(0, tk.END)
        
        def save():
            new_value = var.get()
            new_values = list(values)
            new_values[col_idx] = new_value
            tree.item(item, values=new_values)
            
            # Update internal data
            self._update_internal_data(is_home)
            
            dialog.destroy()
        
        tk.Button(
            dialog,
            text="Spara",
            command=save,
            font=("Segoe UI", 10, "bold"),
            bg="#2ecc71",
            fg="white",
            width=10
        ).pack(pady=10)
        
        # Bind Enter key
        dialog.bind('<Return>', lambda e: save())
    
    def _update_internal_data(self, is_home):
        """Update internal player list from tree"""
        tree = self.home_tree if is_home else self.away_tree
        
        players = []
        for item in tree.get_children():
            values = tree.item(item, 'values')
            players.append({
                'nr': values[0],
                'name': values[1],
                'pos': values[2],
                'kategori': values[3]
            })
        
        if is_home:
            self.home_players = players
        else:
            self.away_players = players
    
    def _import_team(self, is_home):
        """Import team lineup"""
        from gui.dialogs import ImportSourceDialog
        
        dialog = ImportSourceDialog(self, self.data_manager, self.vmix_client, self.config)
        self.wait_window(dialog)
        
        if dialog.result:
            lineup_data = dialog.result
            
            # Extract appropriate team
            team_key = 'home' if is_home else 'away'
            
            # Handle different formats
            if isinstance(lineup_data, dict):
                # SweHockey dict format
                if team_key in lineup_data:
                    team_data = lineup_data[team_key]
                    
                    # Set team name
                    if is_home:
                        self.home_team_name.set(team_data.get('team_name', ''))
                    else:
                        self.away_team_name.set(team_data.get('team_name', ''))
                    
                    # Convert players
                    players = []
                    for p in team_data.get('players', []):
                        players.append({
                            'nr': p.get('number', ''),
                            'name': p.get('name', ''),
                            'pos': p.get('position', 'F'),
                            'kategori': self._auto_categorize(p.get('position', 'F'), len(players))
                        })
                    
                    self._populate_tree(players, is_home)
                    
                    # Sync to main app if available
                    self._sync_to_main_app()
            else:
                # LineupData object
                if hasattr(lineup_data, 'home_team') and hasattr(lineup_data, 'away_team'):
                    team_data = lineup_data.home_team if is_home else lineup_data.away_team
                    
                    # Set team names (both full and short)
                    if is_home:
                        self.home_team_name.set(team_data.get('name', ''))
                        self.home_team_short.set(team_data.get('short_name', ''))
                        # Set logos if available
                        if team_data.get('logo_pregame'):
                            self.home_logo_pregame.set(team_data.get('logo_pregame', ''))
                        if team_data.get('logo_teams'):
                            self.home_logo_teams.set(team_data.get('logo_teams', ''))
                    else:
                        self.away_team_name.set(team_data.get('name', ''))
                        self.away_team_short.set(team_data.get('short_name', ''))
                        # Set logos if available
                        if team_data.get('logo_pregame'):
                            self.away_logo_pregame.set(team_data.get('logo_pregame', ''))
                        if team_data.get('logo_teams'):
                            self.away_logo_teams.set(team_data.get('logo_teams', ''))
                    
                    # Convert players
                    players = []
                    for p in team_data.get('players', []):
                        players.append({
                            'nr': p.get('number', ''),
                            'name': p.get('name', ''),
                            'pos': p.get('position', 'F'),
                            'kategori': self._auto_categorize(p.get('position', 'F'), len(players))
                        })
                    
                    self._populate_tree(players, is_home)
                    
                    # Sync to main app if available
                    self._sync_to_main_app()
    
    def _sync_to_main_app(self):
        """Sync lineup data to main app's lineup_state"""
        if not self.main_window or not hasattr(self.main_window, 'lineup_state'):
            return
        
        # Update internal data first
        self._update_internal_data(True)
        self._update_internal_data(False)
        
        # Get lineup data
        lineup_data = self.get_lineup_data()
        
        # Sync to main app's lineup_state
        try:
            # Home team
            self.main_window.lineup_state.home_team_name = lineup_data['home']['name']
            self.main_window.lineup_state.home_players = []
            for p in lineup_data['home'].get('players', []):
                self.main_window.lineup_state.home_players.append({
                    'number': p.get('nr', ''),
                    'name': p.get('name', ''),
                    'position': p.get('pos', 'F'),
                    'kategori': p.get('kategori', '')
                })
            
            # Away team
            self.main_window.lineup_state.away_team_name = lineup_data['away']['name']
            self.main_window.lineup_state.away_players = []
            for p in lineup_data['away'].get('players', []):
                self.main_window.lineup_state.away_players.append({
                    'number': p.get('nr', ''),
                    'name': p.get('name', ''),
                    'position': p.get('pos', 'F'),
                    'kategori': p.get('kategori', '')
                })
            
            print(f"✓ Synced {len(self.main_window.lineup_state.home_players)} home + {len(self.main_window.lineup_state.away_players)} away players to main app")
        except Exception as e:
            print(f"Note: Could not sync to main app: {e}")
    
    def _auto_categorize(self, position, index):
        """Auto-categorize player based on position"""
        pos = position.upper() if position else 'F'
        
        if pos in ['G', 'GK']:
            return f'GK{(index % 2) + 1}'
        elif pos in ['D', 'LD', 'RD']:
            if index % 2 == 0:
                return f'LD{(index // 2) + 1}'
            else:
                return f'RD{((index + 1) // 2)}'
        else:
            # Forward
            remainder = index % 3
            if remainder == 0:
                return f'LW{(index // 3) + 1}'
            elif remainder == 1:
                return f'C{(index // 3) + 1}'
            else:
                return f'RW{(index // 3) + 1}'
    
    def _populate_tree(self, players, is_home):
        """Populate tree with players"""
        tree = self.home_tree if is_home else self.away_tree
        
        # Clear existing
        for item in tree.get_children():
            tree.delete(item)
        
        # Add players
        for player in players:
            tree.insert('', tk.END, values=(
                player.get('nr', ''),
                player.get('name', ''),
                player.get('pos', 'F'),
                player.get('kategori', '')
            ))
        
        # Update internal data
        self._update_internal_data(is_home)
    
    def _add_player(self, is_home):
        """Add new empty player row"""
        tree = self.home_tree if is_home else self.away_tree
        tree.insert('', tk.END, values=('', '', 'F', ''))
    
    def _remove_player(self, is_home):
        """Remove selected player"""
        tree = self.home_tree if is_home else self.away_tree
        
        selection = tree.selection()
        if not selection:
            messagebox.showwarning("Ingen vald", "Välj en spelare att ta bort")
            return
        
        tree.delete(selection[0])
        self._update_internal_data(is_home)
    
    def get_lineup_data(self):
        """Get current lineup data for export"""
        return {
            'home': {
                'name': self.home_team_name.get(),
                'short_name': self.home_team_short.get(),
                'logo_pregame': self.home_logo_pregame.get(),
                'logo_teams': self.home_logo_teams.get(),
                'players': self.home_players
            },
            'away': {
                'name': self.away_team_name.get(),
                'short_name': self.away_team_short.get(),
                'logo_pregame': self.away_logo_pregame.get(),
                'logo_teams': self.away_logo_teams.get(),
                'players': self.away_players
            }
        }
    
    def _export_lineup(self):
        """Export lineup to JSON files"""
        # Update internal data first
        self._update_internal_data(True)
        self._update_internal_data(False)
        
        # Validate
        if not self.home_team_name.get().strip():
            messagebox.showwarning("Saknas", "Hemmalag namn saknas")
            return
        
        if not self.away_team_name.get().strip():
            messagebox.showwarning("Saknas", "Bortalag namn saknas")
            return
        
        # Get export folder
        export_folder = self.config.get("export_folder", "C:\\vMix\\")
        
        if not export_folder:
            messagebox.showwarning("Ingen mapp", "Välj exportmapp i Länkar-fliken först")
            return
        
        # Get lineup data
        lineup_data = self.get_lineup_data()
        
        # Create improved JSON exporter
        from core.json_exporter_v43 import JSONExporterV43
        
        exporter = JSONExporterV43(lineup_data, self.config)
        
        try:
            results = []
            
            # Export lineup.json
            msg = exporter.export_lineup_json(f"{export_folder}/lineup.json")
            results.append(msg)
            
            # Export scoreboard.json
            msg = exporter.export_scoreboard_json(f"{export_folder}/scoreboard.json")
            results.append(msg)
            
            # Export match.json
            msg = exporter.export_match_json(f"{export_folder}/match.json")
            results.append(msg)
            
            # Success
            msg_text = "Export klar!\n\n" + "\n".join(results)
            msg_text += f"\n\nFiler sparade i: {export_folder}"
            
            messagebox.showinfo("Export klar", msg_text)
            
        except Exception as e:
            import traceback
            traceback.print_exc()
            messagebox.showerror("Export misslyckades", f"Fel vid export:\n\n{e}")
