"""
Season Manager Panel
Step 1: Create and manage seasons
"""

import tkinter as tk
from tkinter import ttk, messagebox, simpledialog
from core.data_manager import DataManager
from core.data_models import Season, Series
from typing import Callable, Optional


class SeasonManagerPanel(tk.Frame):
    """Panel for managing seasons"""
    
    def __init__(self, parent, data_manager: DataManager, on_season_select: Optional[Callable] = None):
        super().__init__(parent, bg="#f5f5f5")
        
        self.data_manager = data_manager
        self.on_season_select = on_season_select
        
        self.seasons = self.data_manager.load_seasons()
        self.selected_sport = None
        self.selected_year = None
        
        self._build_ui()
        self._refresh_seasons_list()
    
    def _build_ui(self):
        """Build season manager UI"""
        # Two columns: existing seasons | create new
        left_frame = tk.Frame(self, bg="#f5f5f5")
        left_frame.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=(0, 10))
        
        right_frame = tk.Frame(self, bg="#f5f5f5")
        right_frame.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=(10, 0))
        
        # LEFT: Existing seasons
        self._build_existing_seasons(left_frame)
        
        # RIGHT: Create new season
        self._build_create_season(right_frame)
    
    def _build_existing_seasons(self, parent):
        """Build existing seasons list"""
        # Title
        tk.Label(
            parent,
            text="Befintliga Säsonger",
            font=("Segoe UI", 14, "bold"),
            bg="#f5f5f5",
            fg="#2c3e50"
        ).pack(anchor=tk.W, pady=(0, 10))
        
        # Listbox with scrollbar
        list_frame = tk.Frame(parent, bg="white", relief="solid", bd=1)
        list_frame.pack(fill=tk.BOTH, expand=True)
        
        scrollbar = tk.Scrollbar(list_frame)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        
        self.seasons_listbox = tk.Listbox(
            list_frame,
            font=("Segoe UI", 11),
            yscrollcommand=scrollbar.set,
            selectmode=tk.SINGLE,
            bg="white",
            fg="#2c3e50",
            selectbackground="#3498db",
            selectforeground="white",
            relief="flat",
            bd=0,
            highlightthickness=0
        )
        self.seasons_listbox.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=10, pady=10)
        scrollbar.config(command=self.seasons_listbox.yview)
        
        self.seasons_listbox.bind('<<ListboxSelect>>', self._on_season_select)
        
        # Buttons
        btn_frame = tk.Frame(parent, bg="#f5f5f5")
        btn_frame.pack(fill=tk.X, pady=(10, 0))
        
        tk.Button(
            btn_frame,
            text="✓ Välj",
            font=("Segoe UI", 10, "bold"),
            command=self._select_season,
            bg="#3498db",
            fg="white",
            relief="flat",
            cursor="hand2",
            padx=15,
            pady=8
        ).pack(side=tk.LEFT, padx=(0, 5))
        
        tk.Button(
            btn_frame,
            text="✎ Redigera",
            font=("Segoe UI", 10),
            command=self._edit_season,
            bg="white",
            fg="#2c3e50",
            relief="solid",
            bd=1,
            cursor="hand2",
            padx=15,
            pady=8
        ).pack(side=tk.LEFT, padx=5)
        
        tk.Button(
            btn_frame,
            text="🗑 Ta bort",
            font=("Segoe UI", 10),
            command=self._delete_season,
            bg="#e74c3c",
            fg="white",
            relief="flat",
            cursor="hand2",
            padx=15,
            pady=8
        ).pack(side=tk.RIGHT)
    
    def _build_create_season(self, parent):
        """Build create new season form"""
        # Title
        tk.Label(
            parent,
            text="Skapa Ny Säsong",
            font=("Segoe UI", 14, "bold"),
            bg="#f5f5f5",
            fg="#2c3e50"
        ).pack(anchor=tk.W, pady=(0, 10))
        
        # Form container
        form = tk.Frame(parent, bg="white", relief="solid", bd=1)
        form.pack(fill=tk.BOTH, expand=True, padx=0, pady=0)
        
        form_inner = tk.Frame(form, bg="white")
        form_inner.pack(fill=tk.BOTH, expand=True, padx=20, pady=20)
        
        # Sport
        tk.Label(
            form_inner,
            text="Sport:",
            font=("Segoe UI", 11, "bold"),
            bg="white",
            fg="#2c3e50"
        ).pack(anchor=tk.W, pady=(0, 5))
        
        sport_frame = tk.Frame(form_inner, bg="white")
        sport_frame.pack(fill=tk.X, pady=(0, 15))
        
        self.sport_var = tk.StringVar()
        self.sport_combo = ttk.Combobox(
            sport_frame,
            textvariable=self.sport_var,
            font=("Segoe UI", 11),
            values=["ISHOCKEY", "FOTBOLL", "HANDBOLL"],
            state="normal",
            width=25
        )
        self.sport_combo.pack(side=tk.LEFT, padx=(0, 10))
        self.sport_combo.set("ISHOCKEY")
        
        tk.Button(
            sport_frame,
            text="+ Annan",
            font=("Segoe UI", 9),
            command=self._add_custom_sport,
            bg="#ecf0f1",
            fg="#2c3e50",
            relief="flat",
            cursor="hand2",
            padx=10,
            pady=5
        ).pack(side=tk.LEFT)
        
        # Season year
        tk.Label(
            form_inner,
            text="Säsong:",
            font=("Segoe UI", 11, "bold"),
            bg="white",
            fg="#2c3e50"
        ).pack(anchor=tk.W, pady=(0, 5))
        
        self.year_var = tk.StringVar(value="25/26")
        tk.Entry(
            form_inner,
            textvariable=self.year_var,
            font=("Segoe UI", 11),
            width=28,
            relief="solid",
            bd=1
        ).pack(anchor=tk.W, pady=(0, 15))
        
        # Series
        tk.Label(
            form_inner,
            text="Serier:",
            font=("Segoe UI", 11, "bold"),
            bg="white",
            fg="#2c3e50"
        ).pack(anchor=tk.W, pady=(0, 5))
        
        # Series list
        series_frame = tk.Frame(form_inner, bg="white", relief="solid", bd=1)
        series_frame.pack(fill=tk.BOTH, expand=True, pady=(0, 10))
        
        self.series_listbox = tk.Listbox(
            series_frame,
            font=("Segoe UI", 10),
            height=4,
            bg="white",
            fg="#2c3e50",
            relief="flat",
            bd=0
        )
        self.series_listbox.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        
        # Add series button
        tk.Button(
            form_inner,
            text="+ Lägg till serie",
            font=("Segoe UI", 10),
            command=self._add_series,
            bg="#ecf0f1",
            fg="#2c3e50",
            relief="flat",
            cursor="hand2",
            pady=8
        ).pack(fill=tk.X, pady=(0, 15))
        
        # Create button
        tk.Button(
            form_inner,
            text="SKAPA SÄSONG",
            font=("Segoe UI", 12, "bold"),
            command=self._create_season,
            bg="#27ae60",
            fg="white",
            relief="flat",
            cursor="hand2",
            pady=12
        ).pack(fill=tk.X)
    
    def _refresh_seasons_list(self):
        """Refresh the seasons listbox"""
        self.seasons_listbox.delete(0, tk.END)
        
        self.seasons = self.data_manager.load_seasons()
        
        for sport, sport_seasons in sorted(self.seasons.items()):
            for year in sorted(sport_seasons.keys(), reverse=True):
                season = sport_seasons[year]
                num_series = len(season.series)
                self.seasons_listbox.insert(
                    tk.END,
                    f"{sport} - Säsong {year}  ({num_series} serier)"
                )
    
    def _on_season_select(self, event):
        """Handle season selection from list"""
        selection = self.seasons_listbox.curselection()
        if not selection:
            return
        
        text = self.seasons_listbox.get(selection[0])
        # Parse "ISHOCKEY - Säsong 25/26  (2 serier)"
        parts = text.split(" - Säsong ")
        if len(parts) == 2:
            sport = parts[0]
            year = parts[1].split("  ")[0]
            self.selected_sport = sport
            self.selected_year = year
    
    def _select_season(self):
        """Select and use this season"""
        if not self.selected_sport or not self.selected_year:
            messagebox.showwarning("Ingen vald", "Välj en säsong först")
            return
        
        messagebox.showinfo(
            "Säsong vald",
            f"Säsong {self.selected_sport} {self.selected_year} är nu vald!\n\nGå vidare till nästa steg."
        )
        
        if self.on_season_select:
            self.on_season_select(self.selected_sport, self.selected_year)
    
    def _edit_season(self):
        """Edit selected season"""
        if not self.selected_sport or not self.selected_year:
            messagebox.showwarning("Ingen vald", "Välj en säsong först")
            return
        
        messagebox.showinfo("Redigera", "Redigering kommer i nästa version")
    
    def _delete_season(self):
        """Delete selected season"""
        if not self.selected_sport or not self.selected_year:
            messagebox.showwarning("Ingen vald", "Välj en säsong först")
            return
        
        result = messagebox.askyesno(
            "Bekräfta borttagning",
            f"Är du säker på att du vill ta bort\n{self.selected_sport} - Säsong {self.selected_year}?\n\nDetta kan inte ångras!",
            icon='warning'
        )
        
        if result:
            self.data_manager.delete_season(self.selected_sport, self.selected_year)
            self._refresh_seasons_list()
            messagebox.showinfo("Borttagen", "Säsongen har tagits bort")
    
    def _add_custom_sport(self):
        """Add a custom sport"""
        sport = simpledialog.askstring("Lägg till sport", "Ange sportens namn:")
        if sport:
            sport = sport.upper()
            current_values = list(self.sport_combo['values'])
            if sport not in current_values:
                current_values.append(sport)
                self.sport_combo['values'] = current_values
            self.sport_var.set(sport)
    
    def _add_series(self):
        """Add a series to the new season"""
        # Dialog for series name and number of teams
        dialog = SeriesDialog(self, "Lägg till serie")
        self.wait_window(dialog)
        
        if dialog.result:
            name, num_teams = dialog.result
            self.series_listbox.insert(tk.END, f"{name} ({num_teams} lag)")
    
    def _create_season(self):
        """Create new season"""
        sport = self.sport_var.get().strip()
        year = self.year_var.get().strip()
        
        if not sport or not year:
            messagebox.showwarning("Ofullständigt", "Fyll i sport och säsong")
            return
        
        # Get series from listbox
        series_dict = {}
        for i in range(self.series_listbox.size()):
            text = self.series_listbox.get(i)
            # Parse "NORRA (20 lag)"
            parts = text.split(" (")
            if len(parts) == 2:
                name = parts[0]
                num_teams = int(parts[1].replace(" lag)", ""))
                series_dict[name] = Series(name=name, num_teams=num_teams)
        
        if not series_dict:
            messagebox.showwarning("Inga serier", "Lägg till minst en serie")
            return
        
        # Create season
        season = Season(sport=sport, year=year, series=series_dict)
        self.data_manager.save_season(season)
        
        # Refresh list
        self._refresh_seasons_list()
        
        # Clear form
        self.year_var.set("")
        self.series_listbox.delete(0, tk.END)
        
        messagebox.showinfo(
            "Skapad!",
            f"Säsong {sport} {year} har skapats!\n\nDu kan nu välja den och gå vidare."
        )


class SeriesDialog(tk.Toplevel):
    """Dialog for adding a series"""
    
    def __init__(self, parent, title):
        super().__init__(parent)
        self.title(title)
        self.geometry("350x200")
        self.resizable(False, False)
        
        self.result = None
        
        # Center on parent
        self.transient(parent)
        self.grab_set()
        
        self._build_ui()
    
    def _build_ui(self):
        """Build dialog UI"""
        container = tk.Frame(self, bg="white")
        container.pack(fill=tk.BOTH, expand=True, padx=20, pady=20)
        
        # Series name
        tk.Label(
            container,
            text="Serie namn:",
            font=("Segoe UI", 10, "bold"),
            bg="white"
        ).pack(anchor=tk.W, pady=(0, 5))
        
        self.name_var = tk.StringVar()
        tk.Entry(
            container,
            textvariable=self.name_var,
            font=("Segoe UI", 11),
            width=30
        ).pack(fill=tk.X, pady=(0, 15))
        
        # Number of teams
        tk.Label(
            container,
            text="Antal lag:",
            font=("Segoe UI", 10, "bold"),
            bg="white"
        ).pack(anchor=tk.W, pady=(0, 5))
        
        self.num_var = tk.StringVar(value="20")
        ttk.Combobox(
            container,
            textvariable=self.num_var,
            font=("Segoe UI", 11),
            values=[str(i) for i in range(8, 25)],
            state="readonly",
            width=28
        ).pack(fill=tk.X, pady=(0, 20))
        
        # Buttons
        btn_frame = tk.Frame(container, bg="white")
        btn_frame.pack(fill=tk.X)
        
        tk.Button(
            btn_frame,
            text="Avbryt",
            font=("Segoe UI", 10),
            command=self.destroy,
            bg="white",
            fg="#2c3e50",
            relief="solid",
            bd=1,
            padx=20,
            pady=8
        ).pack(side=tk.LEFT)
        
        tk.Button(
            btn_frame,
            text="Lägg till",
            font=("Segoe UI", 10, "bold"),
            command=self._submit,
            bg="#3498db",
            fg="white",
            relief="flat",
            padx=20,
            pady=8
        ).pack(side=tk.RIGHT)
    
    def _submit(self):
        """Submit dialog"""
        name = self.name_var.get().strip().upper()
        num_teams = int(self.num_var.get())
        
        if not name:
            messagebox.showwarning("Tomt", "Ange serie namn")
            return
        
        self.result = (name, num_teams)
        self.destroy()
