# gui/dialogs.py
"""
Dialog windows for lineup selection and period transitions
Now uses DataSourceManager for all lineup data
"""

import tkinter as tk
from tkinter import ttk, messagebox


class GoalScorerDialog(tk.Toplevel):
    """
    Dialog to select goal scorer from lineup.
    Uses DataSourceManager for lineup data.
    """

    def __init__(self, parent, app, side: str):
        super().__init__(parent)
        self.app = app
        self.side = side
        self.result = None
        
        self.title(f"Välj målskytt - {side.upper()}")
        self.geometry("400x550")
        self.resizable(False, False)
        
        self._build()

    def _build(self):
        # Title
        tk.Label(
            self,
            text=f"Välj målskytt ({self.side.upper()})",
            font=("Segoe UI", 12, "bold")
        ).pack(pady=10)

        # Lineup list
        players = self.app.data_manager.get_players(self.side)
        
        list_frame = tk.Frame(self)
        list_frame.pack(pady=10, padx=10, fill=tk.BOTH, expand=True)
        
        scrollbar = tk.Scrollbar(list_frame)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        
        self.listbox = tk.Listbox(
            list_frame,
            width=45,
            height=20,
            font=("Segoe UI", 10),
            yscrollcommand=scrollbar.set
        )
        self.listbox.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar.config(command=self.listbox.yview)
        
        # Populate list
        for player in players:
            num = player.get("number", "")
            name = player.get("name", "")
            display = f"{num:>3}  {name}"
            self.listbox.insert(tk.END, display)
        
        # Buttons
        btn_frame = tk.Frame(self)
        btn_frame.pack(pady=10)
        
        tk.Button(
            btn_frame,
            text="Ingen spelare",
            width=15,
            font=("Segoe UI", 10),
            command=self._on_no_player
        ).grid(row=0, column=0, padx=5)
        
        tk.Button(
            btn_frame,
            text="OK",
            width=12,
            font=("Segoe UI", 10),
            command=self._on_ok
        ).grid(row=0, column=1, padx=5)
        
        tk.Button(
            btn_frame,
            text="Avbryt",
            width=12,
            font=("Segoe UI", 10),
            command=self.destroy
        ).grid(row=0, column=2, padx=5)
        
        # Bind double-click
        self.listbox.bind("<Double-Button-1>", lambda e: self._on_ok())

    def _on_no_player(self):
        """User selected no player - only show goal graphic"""
        self.result = ("", "")  # Empty strings = no player
        self.destroy()

    def _on_ok(self):
        sel = self.listbox.curselection()
        if not sel:
            messagebox.showwarning("Ingen spelare vald", "Välj en spelare från listan.")
            return
        
        line = self.listbox.get(sel[0])
        parts = line.strip().split(None, 1)
        if len(parts) >= 2:
            num = parts[0].strip()
            name = parts[1].strip()
        else:
            num = parts[0].strip() if parts else ""
            name = ""
        
        self.result = (num, name)
        self.destroy()


class PenaltyDialog(tk.Toplevel):
    """
    Dialog to set penalty.
    Allows selecting player and setting time.
    Uses DataSourceManager for lineup data.
    """

    def __init__(self, parent, app, slot: str):
        super().__init__(parent)
        self.app = app
        self.slot = slot
        self.result = None
        
        # Determine side from slot
        self.side = "home" if slot.startswith("H") else "away"
        
        self.title(f"Utvisning {slot}")
        self.geometry("400x650")
        self.resizable(False, False)
        
        self._build()

    def _build(self):
        # Title
        tk.Label(
            self,
            text=f"Utvisning {self.slot}",
            font=("Segoe UI", 12, "bold")
        ).pack(pady=10)

        # Player selection
        tk.Label(
            self,
            text="Välj spelare:",
            font=("Segoe UI", 10)
        ).pack()
        
        players = self.app.data_manager.get_players(self.side)
        
        list_frame = tk.Frame(self)
        list_frame.pack(pady=10, padx=10, fill=tk.BOTH, expand=True)
        
        scrollbar = tk.Scrollbar(list_frame)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        
        self.listbox = tk.Listbox(
            list_frame,
            width=45,
            height=18,
            font=("Segoe UI", 10),
            yscrollcommand=scrollbar.set
        )
        self.listbox.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar.config(command=self.listbox.yview)
        
        for player in players:
            num = player.get("number", "")
            name = player.get("name", "")
            display = f"{num:>3}  {name}"
            self.listbox.insert(tk.END, display)

        # Time input
        time_frame = tk.Frame(self)
        time_frame.pack(pady=10)
        
        tk.Label(
            time_frame,
            text="Tid (MM:SS):",
            font=("Segoe UI", 10)
        ).grid(row=0, column=0, padx=5)
        
        self.time_entry = tk.Entry(
            time_frame,
            width=10,
            font=("Segoe UI", 10),
            justify="center"
        )
        self.time_entry.insert(0, "02:00")
        self.time_entry.grid(row=0, column=1, padx=5)

        # Quick time buttons
        quick_frame = tk.Frame(self)
        quick_frame.pack(pady=5)
        
        tk.Button(
            quick_frame,
            text="2 min",
            width=8,
            command=lambda: self._set_time("02:00")
        ).grid(row=0, column=0, padx=3)
        
        tk.Button(
            quick_frame,
            text="5 min",
            width=8,
            command=lambda: self._set_time("05:00")
        ).grid(row=0, column=1, padx=3)
        
        tk.Button(
            quick_frame,
            text="10 min",
            width=8,
            command=lambda: self._set_time("10:00")
        ).grid(row=0, column=2, padx=3)

        # Buttons
        btn_frame = tk.Frame(self)
        btn_frame.pack(pady=15)
        
        tk.Button(
            btn_frame,
            text="OK",
            width=12,
            font=("Segoe UI", 10),
            command=self._on_ok
        ).grid(row=0, column=0, padx=5)
        
        tk.Button(
            btn_frame,
            text="Avbryt",
            width=12,
            font=("Segoe UI", 10),
            command=self.destroy
        ).grid(row=0, column=1, padx=5)

    def _set_time(self, time_str: str):
        """Set time entry to preset value"""
        self.time_entry.delete(0, tk.END)
        self.time_entry.insert(0, time_str)

    def _on_ok(self):
        sel = self.listbox.curselection()
        if not sel:
            messagebox.showwarning("Ingen spelare vald", "Välj en spelare från listan.")
            return
        
        line = self.listbox.get(sel[0])
        parts = line.strip().split(None, 1)
        if len(parts) >= 1:
            num = parts[0].strip()
        else:
            num = ""
        
        time_str = self.time_entry.get().strip()
        if not time_str:
            messagebox.showwarning("Ogiltig tid", "Ange en giltig tid (MM:SS)")
            return
        
        self.result = (num, time_str)
        self.destroy()


class PeriodEndDialog(tk.Toplevel):
    """
    Dialog shown when clock reaches 00:00.
    Asks: "Gå till nästa period?"
    """

    def __init__(self, parent, current_period: str):
        super().__init__(parent)
        self.result = False
        
        self.title("Periodslut")
        self.geometry("350x150")
        self.resizable(False, False)
        
        # Center on parent
        self.transient(parent)
        self.grab_set()
        
        self._build(current_period)

    def _build(self, current_period: str):
        # Message
        msg = f"Period {current_period} är slut.\n\nGå till nästa period?"
        
        tk.Label(
            self,
            text=msg,
            font=("Segoe UI", 11),
            justify="center"
        ).pack(pady=20)

        # Buttons
        btn_frame = tk.Frame(self)
        btn_frame.pack(pady=10)
        
        tk.Button(
            btn_frame,
            text="JA",
            width=12,
            font=("Segoe UI", 10, "bold"),
            bg="green",
            fg="white",
            command=self._on_yes
        ).grid(row=0, column=0, padx=10)
        
        tk.Button(
            btn_frame,
            text="NEJ",
            width=12,
            font=("Segoe UI", 10, "bold"),
            bg="red",
            fg="white",
            command=self._on_no
        ).grid(row=0, column=1, padx=10)

    def _on_yes(self):
        self.result = True
        self.destroy()

    def _on_no(self):
        self.result = False
        self.destroy()


class NameplateDialog(tk.Toplevel):
    """
    Dialog to show nameplate with HOME/AWAY/ALLMÄN options.
    Allows selecting player or staff member.
    Uses DataSourceManager for lineup data.
    """

    def __init__(self, parent, app, default_team=None):
        super().__init__(parent)
        self.app = app
        self.result = None
        self.default_team = default_team  # Pre-select team if provided
        
        self.title("Namnskylt")
        self.geometry("500x750")
        self.resizable(False, False)
        
        # Center on parent
        self.transient(parent)
        self.grab_set()
        
        self._build()

    def _build(self):
        # Title
        tk.Label(
            self,
            text="Visa Namnskylt",
            font=("Segoe UI", 14, "bold")
        ).pack(pady=15)

        # Set default team or use 'home'
        default = self.default_team if self.default_team else "home"
        self.team_var = tk.StringVar(value=default)
        
        # Team selection buttons (only if no default team provided)
        if not self.default_team:
            team_frame = tk.Frame(self)
            team_frame.pack(pady=10)
            
            tk.Label(
                team_frame,
                text="Välj lag:",
                font=("Segoe UI", 11, "bold")
            ).pack(pady=(0, 10))
            
            btn_container = tk.Frame(team_frame)
            btn_container.pack()
            
            # HOME button
            self.home_btn = tk.Button(
                btn_container,
                text="HEMMA",
                width=12,
                height=2,
                font=("Segoe UI", 10, "bold"),
                command=lambda: self._select_team("home"),
                bg="#4CAF50" if default == "home" else "white",
                fg="white" if default == "home" else "black",
                relief="raised" if default == "home" else "flat",
                bd=3 if default == "home" else 2
            )
            self.home_btn.grid(row=0, column=0, padx=5)
            
            # AWAY button
            self.away_btn = tk.Button(
                btn_container,
                text="BORTA",
                width=12,
                height=2,
                font=("Segoe UI", 10, "bold"),
                command=lambda: self._select_team("away"),
                bg="#F44336" if default == "away" else "white",
                fg="white" if default == "away" else "black",
                relief="raised" if default == "away" else "flat",
                bd=3 if default == "away" else 2
            )
            self.away_btn.grid(row=0, column=1, padx=5)
            
            # GENERAL button
            self.general_btn = tk.Button(
                btn_container,
                text="ALLMÄN",
                width=12,
                height=2,
                font=("Segoe UI", 10, "bold"),
                command=lambda: self._select_team("general"),
                bg="white",
                fg="black",
                relief="flat",
                bd=2
            )
            self.general_btn.grid(row=0, column=2, padx=5)
        else:
            # Show selected team label instead
            team_name = "HEMMALAG" if default == "home" else "BORTALAG" if default == "away" else "ALLMÄN"
            team_color = "#4CAF50" if default == "home" else "#F44336" if default == "away" else "#9C27B0"
            
            tk.Label(
                self,
                text=f"Lag: {team_name}",
                font=("Segoe UI", 12, "bold"),
                fg=team_color
            ).pack(pady=10)

        # Selection section label  
        self.select_label = tk.Label(
            self,
            text="Välj person (spelare först, sedan ledare):",
            font=("Segoe UI", 10, "bold")
        )
        self.select_label.pack(pady=(20, 5))
        
        # Lineup listbox
        self.list_frame = tk.Frame(self)
        self.list_frame.pack(pady=10, padx=20, fill=tk.BOTH, expand=True)
        
        scrollbar = tk.Scrollbar(self.list_frame)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        
        self.listbox = tk.Listbox(
            self.list_frame,
            width=55,
            height=22,
            font=("Segoe UI", 10),
            yscrollcommand=scrollbar.set
        )
        self.listbox.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar.config(command=self.listbox.yview)
        
        # Populate with home team players initially
        self._populate_list()

        # Manual input section (for ALLMÄN)
        self.manual_frame = tk.Frame(self)
        
        tk.Label(
            self.manual_frame,
            text="Namn:",
            font=("Segoe UI", 10)
        ).grid(row=0, column=0, padx=5, pady=5, sticky="e")
        
        self.name_entry = tk.Entry(
            self.manual_frame,
            width=30,
            font=("Segoe UI", 10)
        )
        self.name_entry.grid(row=0, column=1, padx=5, pady=5)
        
        tk.Label(
            self.manual_frame,
            text="Nummer:",
            font=("Segoe UI", 10)
        ).grid(row=1, column=0, padx=5, pady=5, sticky="e")
        
        self.number_entry = tk.Entry(
            self.manual_frame,
            width=10,
            font=("Segoe UI", 10)
        )
        self.number_entry.grid(row=1, column=1, padx=5, pady=5, sticky="w")
        
        tk.Label(
            self.manual_frame,
            text="(Lämna tomt för ledare)",
            font=("Segoe UI", 8),
            fg="#7f8c8d"
        ).grid(row=2, column=1, padx=5, pady=(0, 5), sticky="w")

        # Action buttons
        self.btn_frame = tk.Frame(self)
        self.btn_frame.pack(pady=20)
        
        tk.Button(
            self.btn_frame,
            text="AVBRYT",
            width=15,
            font=("Segoe UI", 11),
            command=self.destroy
        ).pack()
        
        # Bind single-click AND double-click
        self.listbox.bind("<ButtonRelease-1>", lambda e: self._on_list_click())
        self.listbox.bind("<Double-Button-1>", lambda e: self._on_show())
        
        # Trigger initial team selection to load players
        if self.default_team:
            self._select_team(self.default_team)
        else:
            self._select_team("home")

    def _select_team(self, team: str):
        """Handle team selection"""
        self.team_var.set(team)
        
        # Update button styles (only if buttons exist)
        if hasattr(self, 'home_btn'):
            if team == "home":
                self.home_btn.config(bg="#4CAF50", fg="white", relief="raised", bd=3)
                self.away_btn.config(bg="white", fg="black", relief="flat", bd=2)
                self.general_btn.config(bg="white", fg="black", relief="flat", bd=2)
            elif team == "away":
                self.home_btn.config(bg="white", fg="black", relief="flat", bd=2)
                self.away_btn.config(bg="#2196F3", fg="white", relief="raised", bd=3)
                self.general_btn.config(bg="white", fg="black", relief="flat", bd=2)
            else:  # general
                self.home_btn.config(bg="white", fg="black", relief="flat", bd=2)
                self.away_btn.config(bg="white", fg="black", relief="flat", bd=2)
                self.general_btn.config(bg="#FF9800", fg="white", relief="raised", bd=3)
        
        # Show/hide appropriate input method
        if team == "general":
            self.select_label.pack_forget()
            self.list_frame.pack_forget()
            self.manual_frame.pack(pady=10, before=self.btn_frame)
        else:
            self.manual_frame.pack_forget()
            self.select_label.pack(pady=(20, 5))
            self.list_frame.pack(pady=10, padx=20, fill=tk.BOTH, expand=True)
            self._populate_list()
    
    def _populate_list(self):
        """Populate listbox with players first, then staff (separated)"""
        self.listbox.delete(0, tk.END)
        
        team = self.team_var.get()
        if team == "general":
            return
        
        # Store item info for later retrieval  
        self.list_items = []
        
        # Add players
        players = self.app.data_manager.get_players(team)
        for player in players:
            num = player.get("number", "")
            name = player.get("name", "")
            display = f"{num:>3}  {name}"
            self.listbox.insert(tk.END, display)
            self.list_items.append(("player", num, name))
        
        # Add separator if we have both players and staff
        staff = self.app.data_manager.get_staff(team)
        if players and staff:
            self.listbox.insert(tk.END, "─" * 50)
            self.list_items.append(("separator", "", ""))
        
        # Add staff
        for member in staff:
            role = member.get("role", "")
            name = member.get("name", "")
            display = f"     {role}: {name}"  # Indent staff entries
            self.listbox.insert(tk.END, display)
            self.list_items.append(("staff", "", name))

    def _on_list_click(self):
        """Handle single click on list - immediately show nameplate"""
        # Small delay to ensure selection is registered
        self.after(100, self._on_show)
    
    def _on_show(self):
        """Show nameplate"""
        team = self.team_var.get()
        
        if team == "general":
            # Manual input
            name = self.name_entry.get().strip()
            number = self.number_entry.get().strip()
            
            if not name:
                messagebox.showwarning("Ogiltigt namn", "Ange ett namn.")
                return
            
            # Determine type based on whether number is provided
            person_type = "player" if number else "staff"
            self.result = (team, person_type, number, name)
            self.destroy()
        else:
            # Lineup selection using stored list_items
            sel = self.listbox.curselection()
            if not sel:
                messagebox.showwarning("Ingen vald", "Välj en person från listan.")
                return
            
            idx = sel[0]
            
            # Check if separator was selected
            if idx >= len(self.list_items):
                return
            
            person_type, number, name = self.list_items[idx]
            
            if person_type == "separator":
                messagebox.showinfo("Info", "Vänligen välj en spelare eller ledare")
                return
            
            self.result = (team, person_type, number, name)
            self.destroy()


class SimpleInputDialog(tk.Toplevel):
    """Simple input dialog with optional dropdown"""
    
    def __init__(self, parent, title, label, initial_value="", options=None):
        super().__init__(parent)
        self.result = None
        
        self.title(title)
        self.geometry("400x150")
        self.resizable(False, False)
        
        self.transient(parent)
        self.grab_set()
        
        # Label
        tk.Label(
            self,
            text=label,
            font=("Segoe UI", 10)
        ).pack(pady=(20, 5), padx=20)
        
        # Entry or Combobox
        if options:
            self.entry = ttk.Combobox(
                self,
                values=options,
                font=("Segoe UI", 10),
                width=35
            )
            self.entry.set(initial_value)
        else:
            self.entry = tk.Entry(self, width=40, font=("Segoe UI", 10))
            self.entry.insert(0, initial_value)
        
        self.entry.pack(pady=5, padx=20)
        self.entry.focus_set()
        self.entry.select_range(0, tk.END)
        
        # Buttons
        btn_frame = tk.Frame(self)
        btn_frame.pack(pady=20)
        
        tk.Button(
            btn_frame,
            text="OK",
            width=10,
            command=self._on_ok,
            bg="#4CAF50",
            fg="white",
            font=("Segoe UI", 10)
        ).pack(side=tk.LEFT, padx=5)
        
        tk.Button(
            btn_frame,
            text="Avbryt",
            width=10,
            command=self.destroy,
            font=("Segoe UI", 10)
        ).pack(side=tk.LEFT, padx=5)
        
        # Bind Enter key
        self.entry.bind('<Return>', lambda e: self._on_ok())
    
    def _on_ok(self):
        value = self.entry.get().strip()
        if value:
            self.result = value
            self.destroy()


class ImportSourceDialog(tk.Toplevel):
    """
    Dialog for selecting import source
    """
    
    def __init__(self, parent, data_manager=None, vmix_client=None, config=None):
        super().__init__(parent)
        
        self.data_manager = data_manager
        self.vmix_client = vmix_client
        self.config = config or {}
        self.result = None
        
        # Initialize variables
        self.input_var = tk.StringVar()
        self.file_path = tk.StringVar()
        
        self.title("Importera Lineup")
        self.geometry("500x400")
        self.resizable(False, False)
        
        # Make modal
        self.transient(parent)
        self.grab_set()
        
        self._build_ui()
    
    def _build_ui(self):
        """Build dialog UI"""
        # Header
        header = tk.Frame(self, bg="#2c3e50", height=60)
        header.pack(fill=tk.X)
        header.pack_propagate(False)
        
        tk.Label(
            header,
            text="IMPORTERA LINEUP",
            font=("Segoe UI", 14, "bold"),
            bg="#2c3e50",
            fg="white"
        ).pack(pady=15)
        
        # Content
        content = tk.Frame(self, bg="white")
        content.pack(fill=tk.BOTH, expand=True, padx=20, pady=20)
        
        tk.Label(
            content,
            text="Välj källa:",
            font=("Segoe UI", 10, "bold"),
            bg="white"
        ).pack(anchor="w", pady=(0, 10))
        
        # Source selection
        self.source_var = tk.StringVar(value="swehockey")
        
        sources = [
            ("SweHockey (Match ID)", "swehockey"),
            ("API (Match ID eller Club ID)", "api"),
            ("vMix (Läs från inputs)", "vmix"),
            ("Lokal fil (JSON/CSV)", "file")
        ]
        
        for text, value in sources:
            tk.Radiobutton(
                content,
                text=text,
                variable=self.source_var,
                value=value,
                font=("Segoe UI", 10),
                bg="white",
                command=self._on_source_change
            ).pack(anchor="w", pady=5)
        
        # Input frame
        self.input_frame = tk.Frame(content, bg="white")
        self.input_frame.pack(fill=tk.X, pady=20)
        
        self._on_source_change()
        
        # Buttons
        btn_frame = tk.Frame(self, bg="white")
        btn_frame.pack(fill=tk.X, padx=20, pady=(0, 20))
        
        tk.Button(
            btn_frame,
            text="Hämta",
            font=("Segoe UI", 10, "bold"),
            bg="#2ecc71",
            fg="white",
            width=12,
            command=self._on_fetch
        ).pack(side=tk.RIGHT, padx=5)
        
        tk.Button(
            btn_frame,
            text="Avbryt",
            font=("Segoe UI", 10),
            width=12,
            command=self.destroy
        ).pack(side=tk.RIGHT, padx=5)
    
    def _on_source_change(self):
        """Update input fields based on selected source"""
        # Clear input frame
        for widget in self.input_frame.winfo_children():
            widget.destroy()
        
        source = self.source_var.get()
        
        if source == "swehockey":
            tk.Label(
                self.input_frame,
                text="Match ID:",
                font=("Segoe UI", 10),
                bg="white"
            ).pack(side=tk.LEFT, padx=5)
            
            self.input_var = tk.StringVar()
            tk.Entry(
                self.input_frame,
                textvariable=self.input_var,
                font=("Segoe UI", 10),
                width=20
            ).pack(side=tk.LEFT, padx=5)
            
        elif source == "api":
            tk.Label(
                self.input_frame,
                text="Match/Club ID:",
                font=("Segoe UI", 10),
                bg="white"
            ).pack(side=tk.LEFT, padx=5)
            
            self.input_var = tk.StringVar()
            tk.Entry(
                self.input_frame,
                textvariable=self.input_var,
                font=("Segoe UI", 10),
                width=20
            ).pack(side=tk.LEFT, padx=5)
            
        elif source == "file":
            tk.Button(
                self.input_frame,
                text="Välj fil...",
                font=("Segoe UI", 10),
                command=self._browse_file,
                bg="#95a5a6",
                fg="white"
            ).pack(side=tk.LEFT, padx=5)
            
            self.file_path = tk.StringVar()
            tk.Label(
                self.input_frame,
                textvariable=self.file_path,
                font=("Segoe UI", 8),
                bg="white",
                fg="#666"
            ).pack(side=tk.LEFT, padx=5)
    
    def _browse_file(self):
        """Browse for file"""
        from tkinter import filedialog
        
        initial_dir = self.config.get("import_folder", "C:\\")
        
        filename = filedialog.askopenfilename(
            title="Välj lineup-fil",
            initialdir=initial_dir,
            filetypes=[
                ("JSON files", "*.json"),
                ("CSV files", "*.csv"),
                ("All files", "*.*")
            ]
        )
        
        if filename:
            self.file_path.set(filename)
    
    def _on_fetch(self):
        """Fetch lineup from selected source"""
        source = self.source_var.get()
        
        try:
            if source == "swehockey":
                match_id = self.input_var.get().strip()
                if not match_id:
                    messagebox.showwarning("Ingen Match ID", "Ange Match ID")
                    return
                
                # Import from SweHockey
                from core.swehockey_scraper import SweHockeyScraper
                scraper = SweHockeyScraper()
                lineup_data = scraper.scrape_lineup(match_id)
                
                # Return full lineup dict (not combined players)
                self.result = lineup_data
                self.destroy()
                
            elif source == "api":
                match_id = self.input_var.get().strip()
                if not match_id:
                    messagebox.showwarning("Ingen ID", "Ange Match ID eller Club ID")
                    return
                
                # Import from API - build correct URL
                try:
                    # Build lineup URL from match ID
                    base_url = "https://vmix-new.hockeyettan.se/api"
                    lineup_url = f"{base_url}/lineup/{match_id}"
                    
                    from core.data_source import DataSourceManager
                    dsm = DataSourceManager()
                    lineup_data = dsm.load_from_api_lineup(lineup_url)
                    
                    # Return full lineup_data
                    self.result = lineup_data
                    self.destroy()
                    
                except Exception as e:
                    import traceback
                    traceback.print_exc()
                    messagebox.showerror("Import misslyckades", f"API-import misslyckades:\n\n{e}")
                    return
                
            elif source == "vmix":
                # Read from vMix
                if not self.vmix_client:
                    messagebox.showerror("Fel", "Inte ansluten till vMix")
                    return
                
                # Import from vMix using DataSourceManager
                from core.data_source import DataSourceManager
                dsm = DataSourceManager()
                
                try:
                    # Use real config if available, otherwise use defaults
                    vmix_config = self.config if self.config else {
                        "vmix": {
                            "host": "127.0.0.1",
                            "port": 8088
                        },
                        "lineup": {
                            "input_home": "LINEUP HEMMA",
                            "input_away": "LINEUP BORTA"
                        },
                        "scoreboard": {
                            "input": "SCOREBOARD UPPE",
                            "home_name_field": "HomeName.Text",
                            "away_name_field": "AwayName.Text"
                        }
                    }
                    lineup_data = dsm.load_from_vmix(self.vmix_client, vmix_config)
                    
                    # Return full lineup_data
                    self.result = lineup_data
                    self.destroy()
                except Exception as e:
                    messagebox.showerror("Import misslyckades", f"Kunde inte läsa från vMix:\n\n{e}")
                    return
                
            elif source == "file":
                filepath = self.file_path.get().strip()
                if not filepath:
                    messagebox.showwarning("Ingen fil", "Välj en fil")
                    return
                
                # Import from file
                from core.data_source import DataSourceManager
                dsm = DataSourceManager()  # Use default config
                lineup_data = dsm.load_from_file(filepath)
                
                # Convert to player list
                players = self._convert_lineup_to_players(lineup_data)
                self.result = players
                self.destroy()
                
        except Exception as e:
            import traceback
            traceback.print_exc()
            messagebox.showerror("Import misslyckades", f"Fel vid import:\n\n{e}")
    
    def _convert_lineup_to_players(self, lineup_data):
        """Convert LineupData or dict to player list with kategorier"""
        players = []
        
        # Handle different input formats
        if isinstance(lineup_data, dict):
            # SweHockey dict format
            if 'home' in lineup_data and 'away' in lineup_data:
                home_players = lineup_data['home'].get('players', [])
                away_players = lineup_data['away'].get('players', [])
                
                # Convert dict format to simple list
                all_players = []
                for p in home_players + away_players:
                    all_players.append({
                        'number': p.get('number', ''),
                        'name': p.get('name', ''),
                        'position': p.get('position', 'F')
                    })
            else:
                # Unknown dict format
                return []
        else:
            # LineupData object (from API/vMix)
            all_players = []
            
            # LineupData uses home_team/away_team dicts
            if hasattr(lineup_data, 'home_team') and hasattr(lineup_data, 'away_team'):
                home_players = lineup_data.home_team.get('players', [])
                away_players = lineup_data.away_team.get('players', [])
                
                for p in home_players + away_players:
                    all_players.append({
                        'number': p.get('number', ''),
                        'name': p.get('name', ''),
                        'position': p.get('position', 'F')
                    })
            else:
                # Fallback - try old format
                try:
                    for p in lineup_data.home_players + lineup_data.away_players:
                        all_players.append({
                            'number': p.number,
                            'name': p.name,
                            'position': p.position
                        })
                except:
                    return []
        
        # Auto-categorize
        gk_count = 0
        d_count = 0
        f_count = 0
        
        for player in all_players:
            pos = player.get('position', 'F').upper() if player.get('position') else 'F'
            
            if pos in ['G', 'GK']:
                gk_count += 1
                kategori = f'GK{gk_count}'
            elif pos in ['D', 'LD', 'RD']:
                d_count += 1
                # Alternate between LD and RD
                if d_count % 2 == 1:
                    kategori = f'LD{(d_count + 1) // 2}'
                else:
                    kategori = f'RD{d_count // 2}'
            else:
                f_count += 1
                # Distribute into LW/C/RW
                if f_count % 3 == 1:
                    kategori = f'LW{(f_count // 3) + 1}'
                elif f_count % 3 == 2:
                    kategori = f'C{(f_count // 3) + 1}'
                else:
                    kategori = f'RW{(f_count // 3) + 1}'
            
            players.append({
                'nr': player.get('number', ''),
                'name': player.get('name', ''),
                'pos': pos if pos in ['GK', 'D', 'F'] else 'F',
                'kategori': kategori
            })
        
        return players


class VMixConnectionDialog(tk.Toplevel):
    """
    Simple vMix connection dialog shown at startup
    """
    
    def __init__(self, parent, config):
        super().__init__(parent)
        
        self.config = config
        self.result = None
        
        self.title("Anslut till vMix")
        self.geometry("450x300")
        self.resizable(False, False)
        
        # Make modal
        self.transient(parent)
        self.grab_set()
        
        self._build_ui()
    
    def _build_ui(self):
        """Build dialog UI"""
        # Header
        header = tk.Frame(self, bg="#2c3e50", height=60)
        header.pack(fill=tk.X)
        header.pack_propagate(False)
        
        tk.Label(
            header,
            text="ANSLUT TILL vMix",
            font=("Segoe UI", 14, "bold"),
            bg="#2c3e50",
            fg="white"
        ).pack(pady=15)
        
        # Content
        content = tk.Frame(self, bg="white")
        content.pack(fill=tk.BOTH, expand=True, padx=30, pady=20)
        
        # Get current config
        vmix_cfg = self.config.get("vmix", {})
        
        # Host
        tk.Label(
            content,
            text="vMix IP/Host:",
            font=("Segoe UI", 10, "bold"),
            bg="white"
        ).grid(row=0, column=0, sticky="w", pady=10)
        
        self.host_var = tk.StringVar(value=vmix_cfg.get("host", "127.0.0.1"))
        tk.Entry(
            content,
            textvariable=self.host_var,
            font=("Segoe UI", 10),
            width=25
        ).grid(row=0, column=1, padx=10, pady=10)
        
        # Port
        tk.Label(
            content,
            text="Port:",
            font=("Segoe UI", 10, "bold"),
            bg="white"
        ).grid(row=1, column=0, sticky="w", pady=10)
        
        self.port_var = tk.StringVar(value=str(vmix_cfg.get("port", 8088)))
        tk.Entry(
            content,
            textvariable=self.port_var,
            font=("Segoe UI", 10),
            width=25
        ).grid(row=1, column=1, padx=10, pady=10)
        
        # Password (optional)
        tk.Label(
            content,
            text="Lösenord:",
            font=("Segoe UI", 10, "bold"),
            bg="white"
        ).grid(row=2, column=0, sticky="w", pady=10)
        
        self.password_var = tk.StringVar(value=vmix_cfg.get("password", ""))
        tk.Entry(
            content,
            textvariable=self.password_var,
            font=("Segoe UI", 10),
            width=25,
            show="*"
        ).grid(row=2, column=1, padx=10, pady=10)
        
        tk.Label(
            content,
            text="(valfritt)",
            font=("Segoe UI", 8),
            bg="white",
            fg="#999"
        ).grid(row=2, column=2, sticky="w")
        
        # Buttons
        btn_frame = tk.Frame(self, bg="white")
        btn_frame.pack(fill=tk.X, padx=30, pady=(0, 20))
        
        tk.Button(
            btn_frame,
            text="Anslut",
            font=("Segoe UI", 10, "bold"),
            bg="#2ecc71",
            fg="white",
            width=12,
            command=self._on_connect
        ).pack(side=tk.RIGHT, padx=5)
        
        tk.Button(
            btn_frame,
            text="Hoppa över",
            font=("Segoe UI", 10),
            width=12,
            command=self._on_skip
        ).pack(side=tk.RIGHT, padx=5)
        
        # Bind Enter key
        self.bind('<Return>', lambda e: self._on_connect())
    
    def _on_connect(self):
        """Handle connect button"""
        host = self.host_var.get().strip()
        port_str = self.port_var.get().strip()
        password = self.password_var.get().strip()
        
        if not host:
            messagebox.showwarning("Fel", "Ange vMix host/IP")
            return
        
        try:
            port = int(port_str)
        except ValueError:
            messagebox.showwarning("Fel", "Port måste vara ett nummer")
            return
        
        # Return result
        self.result = (host, port, password if password else None)
        self.destroy()
    
    def _on_skip(self):
        """Handle skip button"""
        self.result = None
        self.destroy()
