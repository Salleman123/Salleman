# gui/lineup_preview_dialog.py
"""
Preview dialog for lineup data before accepting
"""

import tkinter as tk
from tkinter import ttk, scrolledtext


class LineupPreviewDialog(tk.Toplevel):
    """
    Shows lineup data for preview before accepting.
    User can: GODKÄNN (accept), LÄSA OM (reload), AVBRYT (cancel)
    """
    
    def __init__(self, parent, lineup_data, source_info=""):
        """
        Args:
            parent: Parent window
            lineup_data: Dict with structure:
                {
                    'home': {
                        'team_name': str,
                        'players': [{'number': str, 'name': str, 'position': str}],
                        'staff': [{'role': str, 'name': str}]
                    },
                    'away': {same structure}
                }
            source_info: String describing source (e.g. "SweHockey (Match 1010654)")
        """
        super().__init__(parent)
        self.lineup_data = lineup_data
        self.source_info = source_info
        self.result = None  # Will be 'accept', 'reload', or None (cancel)
        
        # Store tree widgets for editing (changed from text widgets)
        self.home_players_tree = None
        self.away_players_tree = None
        self.home_staff_tree = None  # NEW
        self.away_staff_tree = None  # NEW
        
        self.title("Förhandsgranska laguppställning")
        self.geometry("800x700")
        self.resizable(True, True)
        
        # Make modal
        self.transient(parent)
        self.grab_set()
        
        self._build()
        
        # Center on screen
        self.update_idletasks()
        x = (self.winfo_screenwidth() // 2) - (self.winfo_width() // 2)
        y = (self.winfo_screenheight() // 2) - (self.winfo_height() // 2)
        self.geometry(f'+{x}+{y}')
    
    def _build(self):
        # Title
        title_frame = tk.Frame(self, bg="#2c3e50", height=60)
        title_frame.pack(fill=tk.X)
        title_frame.pack_propagate(False)
        
        tk.Label(
            title_frame,
            text="Förhandsgranska laguppställning",
            font=("Segoe UI", 16, "bold"),
            bg="#2c3e50",
            fg="white"
        ).pack(pady=15)
        
        # Source info
        if self.source_info:
            info_frame = tk.Frame(self, bg="#ecf0f1")
            info_frame.pack(fill=tk.X, pady=(10, 0))
            
            tk.Label(
                info_frame,
                text=f"Källa: {self.source_info}",
                font=("Segoe UI", 10),
                bg="#ecf0f1",
                fg="#2c3e50"
            ).pack(pady=8)
        
        # Scrollable content area
        canvas_frame = tk.Frame(self)
        canvas_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        # Create canvas with scrollbar
        canvas = tk.Canvas(canvas_frame, bg="white")
        scrollbar = ttk.Scrollbar(canvas_frame, orient="vertical", command=canvas.yview)
        scrollable_frame = tk.Frame(canvas, bg="white")
        
        scrollable_frame.bind(
            "<Configure>",
            lambda e: canvas.configure(scrollregion=canvas.bbox("all"))
        )
        
        canvas.create_window((0, 0), window=scrollable_frame, anchor="nw")
        canvas.configure(yscrollcommand=scrollbar.set)
        
        canvas.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")
        
        # Build team sections
        self._build_team_section(scrollable_frame, "HEMMALAG", "home", self.lineup_data.get('home', {}), "#e8f5e9")
        self._build_team_section(scrollable_frame, "BORTALAG", "away", self.lineup_data.get('away', {}), "#ffebee")
        
        # Buttons
        btn_frame = tk.Frame(self, bg="#ecf0f1")
        btn_frame.pack(fill=tk.X, pady=10)
        
        tk.Button(
            btn_frame,
            text="GODKÄNN",
            font=("Segoe UI", 12, "bold"),
            width=15,
            height=2,
            command=self._on_accept,
            bg="#4CAF50",
            fg="white",
            relief="raised",
            bd=3
        ).pack(side=tk.LEFT, padx=(20, 10))
        
        tk.Button(
            btn_frame,
            text="LÄSA OM",
            font=("Segoe UI", 12),
            width=15,
            height=2,
            command=self._on_reload,
            bg="#FF9800",
            fg="white",
            relief="raised",
            bd=2
        ).pack(side=tk.LEFT, padx=10)
        
        tk.Button(
            btn_frame,
            text="AVBRYT",
            font=("Segoe UI", 12),
            width=15,
            height=2,
            command=self._on_cancel,
            bg="#9E9E9E",
            fg="white",
            relief="raised",
            bd=2
        ).pack(side=tk.LEFT, padx=10)
    
    def _build_team_section(self, parent, title, team_id, team_data, bg_color):
        """Build a section for one team - now with EDITABLE text fields!"""
        # Team frame
        team_frame = tk.Frame(parent, bg=bg_color, relief="solid", bd=2)
        team_frame.pack(fill=tk.X, padx=10, pady=10)
        
        # Team name header
        tk.Label(
            team_frame,
            text=f"{title}: {team_data.get('team_name', '(Inget lag)')}",
            font=("Segoe UI", 14, "bold"),
            bg=bg_color,
            fg="#2e7d32" if "HEMMA" in title else "#c62828"
        ).pack(pady=(10, 5), padx=10, anchor="w")
        
        # Players section
        players = team_data.get('players', [])
        if players:
            # Header with edit hint
            header_frame = tk.Frame(team_frame, bg=bg_color)
            header_frame.pack(pady=(10, 5), padx=10, fill=tk.X)
            
            tk.Label(
                header_frame,
                text=f"SPELARE ({len(players)}):",
                font=("Segoe UI", 11, "bold"),
                bg=bg_color
            ).pack(side=tk.LEFT)
            
            tk.Label(
                header_frame,
                text="← Dubbelklicka rad för att redigera",
                font=("Segoe UI", 9, "italic"),
                bg=bg_color,
                fg="#666"
            ).pack(side=tk.LEFT, padx=10)
            
            # 3-column Treeview for players (editable via double-click)
            tree_frame = tk.Frame(team_frame, bg=bg_color)
            tree_frame.pack(pady=(0, 10), padx=20, fill=tk.BOTH, expand=True)
            
            # Create Treeview with 3 columns
            columns = ('number', 'name', 'position')
            players_tree = ttk.Treeview(
                tree_frame,
                columns=columns,
                show='headings',
                height=min(15, len(players)),
                selectmode='browse'
            )
            
            # Define column headings
            players_tree.heading('number', text='NR')
            players_tree.heading('name', text='NAMN')
            players_tree.heading('position', text='POS')
            
            # Define column widths
            players_tree.column('number', width=50, anchor='center')
            players_tree.column('name', width=300, anchor='w')
            players_tree.column('position', width=50, anchor='center')
            
            # Add scrollbar
            scrollbar = ttk.Scrollbar(tree_frame, orient='vertical', command=players_tree.yview)
            players_tree.configure(yscrollcommand=scrollbar.set)
            
            scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
            players_tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
            
            # Bind double-click for editing
            players_tree.bind('<Double-Button-1>', lambda e: self._edit_tree_item(players_tree, e))
            
            # Add players to tree
            for p in players:
                nr = p.get('number', '??')
                name = p.get('name', 'OKÄND')
                pos = p.get('position', 'F')
                players_tree.insert('', tk.END, values=(nr, name, pos))
            
            # Save reference for later
            if team_id == "home":
                self.home_players_tree = players_tree
            else:
                self.away_players_tree = players_tree
            
            # Add delete button for players
            player_btn_frame = tk.Frame(team_frame, bg=bg_color)
            player_btn_frame.pack(pady=5, padx=20, fill=tk.X)
            
            tk.Button(
                player_btn_frame,
                text="− Ta bort vald spelare",
                command=lambda: self._delete_player(players_tree),
                font=("Segoe UI", 9),
                bg="#f44336",
                fg="white"
            ).pack(side=tk.LEFT)
        else:
            tk.Label(
                team_frame,
                text="Inga spelare",
                font=("Segoe UI", 10, "italic"),
                bg=bg_color,
                fg="#666"
            ).pack(pady=5, padx=10, anchor="w")
        
        # Visual separator between players and staff
        ttk.Separator(team_frame, orient='horizontal').pack(fill=tk.X, padx=20, pady=15)
        
        # Staff section
        staff = team_data.get('staff', [])
        if staff:
            staff_header_frame = tk.Frame(team_frame, bg=bg_color)
            staff_header_frame.pack(pady=(10, 0), padx=10, fill=tk.X)
            
            tk.Label(
                staff_header_frame,
                text=f"LEDARE ({len(staff)}):",
                font=("Segoe UI", 11, "bold"),
                bg=bg_color
            ).pack(side=tk.LEFT)
            
            tk.Label(
                staff_header_frame,
                text="← Dubbelklicka rad för att redigera",
                font=("Segoe UI", 9, "italic"),
                bg=bg_color,
                fg="#666"
            ).pack(side=tk.LEFT, padx=10)
            
            # Treeview for staff (editable via double-click)
            staff_tree_frame = tk.Frame(team_frame, bg=bg_color)
            staff_tree_frame.pack(pady=(5, 10), padx=20, fill=tk.BOTH)
            
            # Create Treeview with 2 columns
            staff_columns = ('role', 'name')
            staff_tree = ttk.Treeview(
                staff_tree_frame,
                columns=staff_columns,
                show='headings',
                height=min(5, len(staff)),
                selectmode='browse'
            )
            
            # Define column headings
            staff_tree.heading('role', text='ROLL')
            staff_tree.heading('name', text='NAMN')
            
            # Define column widths
            staff_tree.column('role', width=150, anchor='w')
            staff_tree.column('name', width=250, anchor='w')
            
            # Add scrollbar
            staff_scrollbar = ttk.Scrollbar(staff_tree_frame, orient='vertical', command=staff_tree.yview)
            staff_tree.configure(yscrollcommand=staff_scrollbar.set)
            
            staff_scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
            staff_tree.pack(side=tk.LEFT, fill=tk.BOTH)
            
            # Bind double-click for editing
            staff_tree.bind('<Double-Button-1>', lambda e: self._edit_staff_item(staff_tree, e))
            
            # Add staff to tree
            for s in staff:
                role = s.get('role', '?')
                name = s.get('name', 'OKÄND')
                staff_tree.insert('', tk.END, values=(role, name))
            
            # Save reference for later
            if team_id == "home":
                self.home_staff_tree = staff_tree
            else:
                self.away_staff_tree = staff_tree
            
            # Add button for adding more staff
            add_btn_frame = tk.Frame(team_frame, bg=bg_color)
            add_btn_frame.pack(pady=5, padx=20, fill=tk.X)
            
            tk.Button(
                add_btn_frame,
                text="+ Lägg till ledare",
                command=lambda: self._add_staff(team_id, staff_tree),
                font=("Segoe UI", 9),
                bg="#2196F3",
                fg="white"
            ).pack(side=tk.LEFT, padx=(0, 5))
            
            tk.Button(
                add_btn_frame,
                text="− Ta bort vald",
                command=lambda: self._delete_staff(staff_tree),
                font=("Segoe UI", 9),
                bg="#f44336",
                fg="white"
            ).pack(side=tk.LEFT)
            
            # Add spacing at bottom
            tk.Label(team_frame, text="", bg=bg_color).pack(pady=5)
        else:
            # No staff - show message and button to add
            tk.Label(
                team_frame,
                text="Inga ledare",
                font=("Segoe UI", 10, "italic"),
                bg=bg_color,
                fg="#666"
            ).pack(pady=5, padx=10, anchor="w")
            
            # Create empty tree for adding staff
            staff_tree_frame = tk.Frame(team_frame, bg=bg_color)
            staff_tree_frame.pack(pady=(5, 10), padx=20, fill=tk.BOTH)
            
            staff_columns = ('role', 'name')
            staff_tree = ttk.Treeview(
                staff_tree_frame,
                columns=staff_columns,
                show='headings',
                height=3,
                selectmode='browse'
            )
            
            staff_tree.heading('role', text='ROLL')
            staff_tree.heading('name', text='NAMN')
            staff_tree.column('role', width=150, anchor='w')
            staff_tree.column('name', width=250, anchor='w')
            
            staff_tree.pack(fill=tk.BOTH)
            
            # Bind double-click
            staff_tree.bind('<Double-Button-1>', lambda e: self._edit_staff_item(staff_tree, e))
            
            # Save reference
            if team_id == "home":
                self.home_staff_tree = staff_tree
            else:
                self.away_staff_tree = staff_tree
            
            # Add button
            add_btn_frame = tk.Frame(team_frame, bg=bg_color)
            add_btn_frame.pack(pady=5, padx=20, fill=tk.X)
            
            tk.Button(
                add_btn_frame,
                text="+ Lägg till ledare",
                command=lambda: self._add_staff(team_id, staff_tree),
                font=("Segoe UI", 9),
                bg="#4CAF50",
                fg="white"
            ).pack(side=tk.LEFT)
    
    def _on_accept(self):
        """User accepts the lineup - parse any edited data from Treeview first"""
        # Parse edited player data from tree widgets
        if self.home_players_tree:
            self._parse_tree_players('home', self.home_players_tree)
        
        if self.away_players_tree:
            self._parse_tree_players('away', self.away_players_tree)
        
        # Parse edited staff data from tree widgets
        if self.home_staff_tree:
            self._parse_tree_staff('home', self.home_staff_tree)
        
        if self.away_staff_tree:
            self._parse_tree_staff('away', self.away_staff_tree)
        
        self.result = 'accept'
        self.destroy()
    
    def _parse_tree_players(self, team_id, tree_widget):
        """Parse Treeview data back into lineup_data"""
        try:
            new_players = []
            
            # Get all items from tree
            for item_id in tree_widget.get_children():
                values = tree_widget.item(item_id)['values']
                if len(values) >= 3:
                    number = str(values[0])
                    name = str(values[1])
                    position = str(values[2]) if values[2] in ['F', 'D', 'G'] else 'F'
                    
                    new_players.append({
                        'number': number,
                        'name': name,
                        'position': position
                    })
            
            # Update lineup_data
            if new_players:
                self.lineup_data[team_id]['players'] = new_players
                
        except Exception as e:
            print(f"Error parsing tree players: {e}")
            # If parsing fails, keep original data
    
    def _parse_tree_staff(self, team_id, tree_widget):
        """Parse staff Treeview data back into lineup_data"""
        try:
            new_staff = []
            
            # Get all items from tree
            for item_id in tree_widget.get_children():
                values = tree_widget.item(item_id)['values']
                if len(values) >= 2:
                    role = str(values[0])
                    name = str(values[1])
                    
                    new_staff.append({
                        'role': role,
                        'name': name
                    })
            
            # Update lineup_data
            if new_staff:
                self.lineup_data[team_id]['staff'] = new_staff
                
        except Exception as e:
            print(f"Error parsing tree staff: {e}")
            # If parsing fails, keep original data
    
    def _edit_tree_item(self, tree, event):
        """Edit selected tree item on double-click"""
        # Get selected item
        selection = tree.selection()
        if not selection:
            return
        
        item_id = selection[0]
        values = tree.item(item_id)['values']
        
        if len(values) < 3:
            return
        
        # Create edit dialog
        dialog = tk.Toplevel(self)
        dialog.title("Redigera spelare")
        dialog.geometry("400x200")
        dialog.transient(self)
        dialog.grab_set()
        
        # Nummer
        tk.Label(dialog, text="Nummer:", font=("Segoe UI", 10)).grid(
            row=0, column=0, sticky=tk.W, padx=10, pady=5
        )
        number_entry = tk.Entry(dialog, width=10, font=("Segoe UI", 10))
        number_entry.insert(0, str(values[0]))
        number_entry.grid(row=0, column=1, sticky=tk.W, padx=10, pady=5)
        
        # Namn
        tk.Label(dialog, text="Namn:", font=("Segoe UI", 10)).grid(
            row=1, column=0, sticky=tk.W, padx=10, pady=5
        )
        name_entry = tk.Entry(dialog, width=30, font=("Segoe UI", 10))
        name_entry.insert(0, str(values[1]))
        name_entry.grid(row=1, column=1, sticky=tk.W, padx=10, pady=5)
        
        # Position
        tk.Label(dialog, text="Position:", font=("Segoe UI", 10)).grid(
            row=2, column=0, sticky=tk.W, padx=10, pady=5
        )
        position_var = tk.StringVar(value=str(values[2]))
        position_frame = tk.Frame(dialog)
        position_frame.grid(row=2, column=1, sticky=tk.W, padx=10, pady=5)
        
        for pos in ['F', 'D', 'G']:
            tk.Radiobutton(
                position_frame,
                text=pos,
                variable=position_var,
                value=pos,
                font=("Segoe UI", 10)
            ).pack(side=tk.LEFT, padx=5)
        
        # Buttons
        def save():
            new_values = (
                number_entry.get().strip(),
                name_entry.get().strip().upper(),
                position_var.get()
            )
            tree.item(item_id, values=new_values)
            dialog.destroy()
        
        def cancel():
            dialog.destroy()
        
        btn_frame = tk.Frame(dialog)
        btn_frame.grid(row=3, column=0, columnspan=2, pady=20)
        
        tk.Button(
            btn_frame,
            text="Spara",
            width=10,
            command=save,
            bg="#4CAF50",
            fg="white",
            font=("Segoe UI", 10, "bold")
        ).pack(side=tk.LEFT, padx=5)
        
        tk.Button(
            btn_frame,
            text="Avbryt",
            width=10,
            command=cancel,
            font=("Segoe UI", 10)
        ).pack(side=tk.LEFT, padx=5)
        
        # Focus name field
        name_entry.focus_set()
        name_entry.select_range(0, tk.END)
    
    def _edit_staff_item(self, tree, event):
        """Edit selected staff item on double-click"""
        # Get selected item
        selection = tree.selection()
        if not selection:
            return
        
        item_id = selection[0]
        values = tree.item(item_id)['values']
        
        if len(values) < 2:
            return
        
        # Create edit dialog
        dialog = tk.Toplevel(self)
        dialog.title("Redigera ledare")
        dialog.geometry("400x150")
        dialog.transient(self)
        dialog.grab_set()
        
        # Roll
        tk.Label(dialog, text="Roll:", font=("Segoe UI", 10)).grid(
            row=0, column=0, sticky=tk.W, padx=10, pady=5
        )
        role_entry = tk.Entry(dialog, width=30, font=("Segoe UI", 10))
        role_entry.insert(0, str(values[0]))
        role_entry.grid(row=0, column=1, sticky=tk.W, padx=10, pady=5)
        
        # Namn
        tk.Label(dialog, text="Namn:", font=("Segoe UI", 10)).grid(
            row=1, column=0, sticky=tk.W, padx=10, pady=5
        )
        name_entry = tk.Entry(dialog, width=30, font=("Segoe UI", 10))
        name_entry.insert(0, str(values[1]))
        name_entry.grid(row=1, column=1, sticky=tk.W, padx=10, pady=5)
        
        # Buttons
        def save():
            new_values = (
                role_entry.get().strip(),
                name_entry.get().strip().upper()
            )
            tree.item(item_id, values=new_values)
            dialog.destroy()
        
        def cancel():
            dialog.destroy()
        
        btn_frame = tk.Frame(dialog)
        btn_frame.grid(row=2, column=0, columnspan=2, pady=20)
        
        tk.Button(
            btn_frame,
            text="Spara",
            width=10,
            command=save,
            bg="#4CAF50",
            fg="white",
            font=("Segoe UI", 10, "bold")
        ).pack(side=tk.LEFT, padx=5)
        
        tk.Button(
            btn_frame,
            text="Avbryt",
            width=10,
            command=cancel,
            font=("Segoe UI", 10)
        ).pack(side=tk.LEFT, padx=5)
        
        # Focus name field
        name_entry.focus_set()
        name_entry.select_range(0, tk.END)
    
    def _add_staff(self, team_id, staff_tree):
        """Add new staff member to tree"""
        # Create dialog
        dialog = tk.Toplevel(self)
        dialog.title("Lägg till ledare")
        dialog.geometry("400x150")
        dialog.transient(self)
        dialog.grab_set()
        
        # Roll
        tk.Label(dialog, text="Roll:", font=("Segoe UI", 10)).grid(
            row=0, column=0, sticky=tk.W, padx=10, pady=5
        )
        role_entry = tk.Entry(dialog, width=30, font=("Segoe UI", 10))
        role_entry.insert(0, "Huvudtränare")
        role_entry.grid(row=0, column=1, sticky=tk.W, padx=10, pady=5)
        
        # Namn
        tk.Label(dialog, text="Namn:", font=("Segoe UI", 10)).grid(
            row=1, column=0, sticky=tk.W, padx=10, pady=5
        )
        name_entry = tk.Entry(dialog, width=30, font=("Segoe UI", 10))
        name_entry.grid(row=1, column=1, sticky=tk.W, padx=10, pady=5)
        
        # Buttons
        def add():
            role = role_entry.get().strip()
            name = name_entry.get().strip().upper()
            
            if role and name:
                staff_tree.insert('', tk.END, values=(role, name))
                dialog.destroy()
        
        def cancel():
            dialog.destroy()
        
        btn_frame = tk.Frame(dialog)
        btn_frame.grid(row=2, column=0, columnspan=2, pady=20)
        
        tk.Button(
            btn_frame,
            text="Lägg till",
            width=10,
            command=add,
            bg="#4CAF50",
            fg="white",
            font=("Segoe UI", 10, "bold")
        ).pack(side=tk.LEFT, padx=5)
        
        tk.Button(
            btn_frame,
            text="Avbryt",
            width=10,
            command=cancel,
            font=("Segoe UI", 10)
        ).pack(side=tk.LEFT, padx=5)
        
        # Focus name field
        name_entry.focus_set()
    
    def _delete_player(self, players_tree):
        """Delete selected player from tree"""
        selection = players_tree.selection()
        if not selection:
            from tkinter import messagebox
            messagebox.showwarning("Ingen vald", "Välj en spelare att ta bort")
            return
        
        players_tree.delete(selection[0])
    
    def _delete_staff(self, staff_tree):
        """Delete selected staff member from tree"""
        selection = staff_tree.selection()
        if not selection:
            from tkinter import messagebox
            messagebox.showwarning("Ingen vald", "Välj en ledare att ta bort")
            return
        
        staff_tree.delete(selection[0])
    
    def _on_reload(self):
        """User wants to reload from source"""
        self.result = 'reload'
        self.destroy()
    
    def _on_cancel(self):
        """User cancels"""
        self.result = None
        self.destroy()
