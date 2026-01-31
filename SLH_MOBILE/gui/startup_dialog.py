# gui/startup_dialog.py
"""
Startup dialog for loading lineup data before match starts
"""

import tkinter as tk
from tkinter import ttk, messagebox, filedialog
import os
import sys
from datetime import datetime

# Add parent directory to path for imports
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from core.swehockey_scraper import SweHockeyScraper, SweHockeyScraperError
from core.lineup_parsers import LineupParsers, LineupParseError
from gui.lineup_preview_dialog import LineupPreviewDialog


class StartupDialog(tk.Toplevel):
    """
    Dialog shown at startup to load lineup data.
    Options:
    1. Load from vMix (reads lineup inputs once)
    2. Load from file (previous saved lineup)
    3. Create manually (enter teams and add staff)
    """
    
    def __init__(self, parent, data_manager, vmix_client, config):
        super().__init__(parent)
        self.data_manager = data_manager
        self.vmix_client = vmix_client
        self.config = config
        self.result = None  # Will be LineupData or None
        
        self.title("SLH - Ladda laguppställning")
        self.geometry("650x900")
        self.resizable(True, True)  # Allow resizing
        
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
            text="Ladda laguppställning",
            font=("Segoe UI", 16, "bold"),
            bg="#2c3e50",
            fg="white"
        ).pack(pady=15)
        
        # Main content
        main = tk.Frame(self, bg="#ecf0f1")
        main.pack(fill=tk.BOTH, expand=True, padx=20, pady=20)
        
        # Instructions
        tk.Label(
            main,
            text="Välj hur du vill ladda laguppställningar och ledare:",
            font=("Segoe UI", 11),
            bg="#ecf0f1",
            justify=tk.LEFT
        ).pack(anchor=tk.W, pady=(0, 20))
        
        # ============================================
        # Option 1: Load from vMix (NO FRAME)
        # ============================================
        tk.Label(
            main,
            text="1. Hämta från vMix",
            font=("Segoe UI", 11, "bold"),
            bg="#ecf0f1"
        ).pack(anchor=tk.W, pady=(10, 5))
        
        tk.Label(
            main,
            text="Läser spelarlista från vMix LINEUP-inputs.\nDu kan sedan lägga till ledare/tränare manuellt.",
            font=("Segoe UI", 10),
            bg="#ecf0f1",
            justify=tk.LEFT
        ).pack(anchor=tk.W, pady=(0, 10))
        
        tk.Button(
            main,
            text="HÄMTA FRÅN vMix",
            font=("Segoe UI", 10, "bold"),
            command=self._load_from_vmix,
            bg="#3498db",
            fg="white",
            width=25,
            height=2
        ).pack(pady=(0, 20))
        
        # ============================================
        # Option 2: Load from API (NO FRAME)
        # ============================================
        tk.Label(
            main,
            text="2. Hämta från API (Smart)",
            font=("Segoe UI", 11, "bold"),
            bg="#ecf0f1"
        ).pack(anchor=tk.W, pady=(10, 5))
        
        tk.Label(
            main,
            text="Ange Club ID (t.ex. 'demo' för test):",
            font=("Segoe UI", 10),
            bg="#ecf0f1"
        ).pack(anchor=tk.W, pady=(0, 10))
        
        self.club_id_entry = tk.Entry(
            main,
            font=("Segoe UI", 10),
            width=30
        )
        self.club_id_entry.insert(0, "demo")
        self.club_id_entry.pack(anchor=tk.W, pady=(0, 10))
        
        tk.Button(
            main,
            text="HÄMTA FRÅN API",
            font=("Segoe UI", 10, "bold"),
            command=self._load_from_api_smart,
            bg="#e67e22",
            fg="white",
            width=25,
            height=2
        ).pack(pady=(0, 20))
        
        # ============================================
        # Option 3: Load from SweHockey
        # ============================================
        tk.Label(
            main,
            text="3. Hämta från SweHockey (Rekommenderad)",
            font=("Segoe UI", 11, "bold"),
            bg="#ecf0f1"
        ).pack(anchor=tk.W, pady=(10, 5))
        
        tk.Label(
            main,
            text="Match-ID från stats.swehockey.se:\n✓ Alltid tillgänglig\n✓ Officiell källa",
            font=("Segoe UI", 10),
            bg="#ecf0f1"
        ).pack(anchor=tk.W, pady=(0, 10))
        
        self.match_id_entry = tk.Entry(
            main,
            font=("Segoe UI", 10),
            width=30
        )
        self.match_id_entry.insert(0, "1010654")
        self.match_id_entry.pack(anchor=tk.W, pady=(0, 10))
        
        tk.Button(
            main,
            text="HÄMTA FRÅN SWEHOCKEY",
            font=("Segoe UI", 10, "bold"),
            command=self._load_from_swehockey,
            bg="#2196F3",
            fg="white",
            width=25,
            height=2
        ).pack(pady=(0, 20))
        
        # ============================================
        # Option 4: Load from file
        # ============================================
        tk.Label(
            main,
            text="4. Ladda från fil",
            font=("Segoe UI", 11, "bold"),
            bg="#ecf0f1"
        ).pack(anchor=tk.W, pady=(10, 5))
        
        tk.Label(
            main,
            text="Ladda tidigare sparad laguppställning från fil.",
            font=("Segoe UI", 10),
            bg="#ecf0f1"
        ).pack(anchor=tk.W, pady=(0, 10))
        
        # File listbox
        self.file_listbox = tk.Listbox(
            main,
            height=5,
            font=("Segoe UI", 9)
        )
        self.file_listbox.pack(fill=tk.X, pady=(0, 10))
        
        # Populate with recent files
        self._populate_file_list()
        
        btn_frame = tk.Frame(main, bg="#ecf0f1")
        btn_frame.pack(fill=tk.X, pady=(0, 20))
        
        tk.Button(
            btn_frame,
            text="LADDA VALD FIL",
            font=("Segoe UI", 9, "bold"),
            command=self._load_selected_file,
            bg="#27ae60",
            fg="white",
            width=15
        ).pack(side=tk.LEFT, padx=(0, 5))
        
        tk.Button(
            btn_frame,
            text="BLÄDDRA",
            font=("Segoe UI", 9),
            command=self._browse_file,
            bg="#7f8c8d",
            fg="white",
            width=15
        ).pack(side=tk.LEFT)
        
        # ============================================
        # Option 5: Create manually
        # ============================================
        tk.Label(
            main,
            text="5. Skapa manuellt",
            font=("Segoe UI", 11, "bold"),
            bg="#ecf0f1"
        ).pack(anchor=tk.W, pady=(10, 5))
        
        tk.Label(
            main,
            text="Skapa tom laguppställning och lägg till allt manuellt.\n(Kan ta tid - rekommenderas ej)",
            font=("Segoe UI", 10),
            bg="#ecf0f1",
            justify=tk.LEFT,
            fg="#7f8c8d"
        ).pack(anchor=tk.W, pady=(0, 10))
        
        tk.Button(
            main,
            text="SKAPA MANUELLT",
            font=("Segoe UI", 10),
            command=self._create_manual,
            bg="#95a5a6",
            fg="white",
            width=25,
            height=2
        ).pack(pady=(0, 20))
        
        # Bottom buttons
        bottom = tk.Frame(self, bg="#ecf0f1")
        bottom.pack(fill=tk.X, padx=20, pady=(0, 20))
        
        tk.Button(
            bottom,
            text="AVBRYT",
            font=("Segoe UI", 10),
            command=self._on_cancel,
            bg="#e74c3c",
            fg="white",
            width=15
        ).pack(side=tk.RIGHT)
    
    def _populate_file_list(self):
        """Populate listbox with recent lineup files"""
        self.file_listbox.delete(0, tk.END)
        
        lineups = self.data_manager.list_saved_lineups()
        
        if not lineups:
            self.file_listbox.insert(tk.END, "  (Inga sparade filer)")
            self.file_listbox.config(state=tk.DISABLED)
            return
        
        for filepath, metadata in lineups[:10]:  # Show max 10
            filename = metadata.get("filename", "")
            created = metadata.get("created", "")
            
            # Format date
            try:
                from datetime import datetime
                dt = datetime.fromisoformat(created)
                date_str = dt.strftime("%Y-%m-%d %H:%M")
            except:
                date_str = created[:16] if len(created) >= 16 else created
            
            display = f"{date_str} - {filename}"
            self.file_listbox.insert(tk.END, display)
        
        # Store filepath mapping
        self.filepath_map = {i: lineups[i][0] for i in range(len(lineups[:10]))}
    
    def _load_from_vmix(self):
        """Load lineup from vMix"""
        try:
            if not self.vmix_client:
                messagebox.showerror("Fel", "Ingen vMix-anslutning tillgänglig")
                return
            
            # Load from vMix
            lineup = self.data_manager.load_from_vmix(self.vmix_client, self.config)
            
            # Show edit dialog to add staff
            edit_dialog = EditLineupDialog(self, self.data_manager, from_vmix=True)
            self.wait_window(edit_dialog)
            
            if edit_dialog.result:
                # Save to file
                try:
                    filepath = self.data_manager.save_to_file()
                    messagebox.showinfo(
                        "Laguppställning sparad",
                        f"Laguppställning har sparats till:\n{filepath}\n\n"
                        "Du kan ladda denna fil nästa gång för att slippa hämta från vMix."
                    )
                except Exception as e:
                    messagebox.showwarning("Varning", f"Kunde inte spara fil:\n{e}")
                
                self.result = self.data_manager.lineup_data
                self.destroy()
            
        except Exception as e:
            messagebox.showerror("Fel", f"Kunde inte hämta från vMix:\n{e}")
    
    def _load_from_api(self):
        """Load lineup from API endpoints"""
        lineup_url = self.lineup_url_entry.get().strip()
        players_url = self.players_url_entry.get().strip()
        
        if not lineup_url or not players_url:
            messagebox.showwarning("Ogiltiga URLs", "Ange både lineup URL och players URL")
            return
        
        try:
            # Show loading message
            loading = tk.Toplevel(self)
            loading.title("Laddar...")
            loading.geometry("300x100")
            loading.transient(self)
            loading.grab_set()
            
            tk.Label(
                loading,
                text="Hämtar data från API...",
                font=("Segoe UI", 11)
            ).pack(pady=30)
            
            loading.update()
            
            # Load from API
            lineup = self.data_manager.load_from_api(lineup_url, players_url)
            
            loading.destroy()
            
            # Show edit dialog to add/edit staff
            edit_dialog = EditLineupDialog(self, self.data_manager, from_vmix=False)
            self.wait_window(edit_dialog)
            
            if edit_dialog.result:
                # Save to file
                try:
                    filepath = self.data_manager.save_to_file()
                    messagebox.showinfo(
                        "Laguppställning sparad",
                        f"Laguppställning har sparats till:\n{filepath}\n\n"
                        "Du kan ladda denna fil nästa gång för att slippa hämta från API."
                    )
                except Exception as e:
                    messagebox.showwarning("Varning", f"Kunde inte spara fil:\n{e}")
                
                self.result = self.data_manager.lineup_data
                self.destroy()
            
        except Exception as e:
            try:
                loading.destroy()
            except:
                pass
            messagebox.showerror("API-fel", f"Kunde inte hämta från API:\n{e}")
    
    def _load_selected_file(self):
        """Load selected file from list"""
        sel = self.file_listbox.curselection()
        if not sel:
            messagebox.showwarning("Ingen fil vald", "Välj en fil från listan")
            return
        
        idx = sel[0]
        if idx not in self.filepath_map:
            return
        
        filepath = self.filepath_map[idx]
        self._load_file(filepath)
    
    def _browse_file(self):
        """Browse for lineup file"""
        filepath = filedialog.askopenfilename(
            title="Välj laguppställning",
            filetypes=[("JSON-filer", "*.json"), ("Alla filer", "*.*")],
            initialdir=self.data_manager.cache_dir
        )
        
        if filepath:
            self._load_file(filepath)
    
    def _load_file(self, filepath: str):
        """Load lineup from file"""
        try:
            lineup = self.data_manager.load_from_file(filepath)
            
            # Show preview/edit dialog
            edit_dialog = EditLineupDialog(self, self.data_manager, from_vmix=False)
            self.wait_window(edit_dialog)
            
            if edit_dialog.result:
                self.result = self.data_manager.lineup_data
                self.destroy()
            
        except Exception as e:
            messagebox.showerror("Fel", f"Kunde inte ladda fil:\n{e}")
    
    def _create_manual(self):
        """Create manual lineup"""
        from core.data_source import LineupData
        
        self.data_manager.lineup_data = LineupData()
        
        # Show edit dialog
        edit_dialog = EditLineupDialog(self, self.data_manager, from_vmix=False)
        self.wait_window(edit_dialog)
        
        if edit_dialog.result:
            # Save to file
            try:
                filepath = self.data_manager.save_to_file()
                messagebox.showinfo("Sparat", f"Laguppställning sparad till:\n{filepath}")
            except Exception as e:
                messagebox.showwarning("Varning", f"Kunde inte spara:\n{e}")
            
            self.result = self.data_manager.lineup_data
            self.destroy()
    
    def _on_cancel(self):
        """Cancel dialog"""
        result = messagebox.askyesno(
            "Avbryt",
            "Avbryta? Applikationen kan inte starta utan laguppställning."
        )
        if result:
            self.result = None
            self.destroy()
    
    def _load_from_api_smart(self):
        """Load lineup from API using Club ID (SMART MODE)"""
        club_id = self.club_id_entry.get().strip()
        
        if not club_id:
            messagebox.showwarning("Ogiltigt Club ID", "Ange ett Club ID (t.ex. 'demo')")
            return
        
        try:
            # Show loading message
            loading = tk.Toplevel(self)
            loading.title("Hämtar från API...")
            loading.geometry("400x150")
            loading.transient(self)
            loading.grab_set()
            
            status_label = tk.Label(
                loading,
                text="Ansluter till API...",
                font=("Segoe UI", 11)
            )
            status_label.pack(pady=30)
            
            loading.update()
            
            # Fetch lineup with Club ID
            status_label.config(text=f"Hämtar laguppställning för {club_id}...")
            loading.update()
            
            lineup_url = f"https://vmix-new.hockeyettan.se/api/lineup/{club_id}"
            players_url = f"https://vmix-new.hockeyettan.se/api/players/{club_id}"
            
            print(f"Fetching from Club ID: {club_id}")
            lineup = self.data_manager.load_from_api(lineup_url, players_url)
            
            loading.destroy()
            
            # Show success with team names
            home_name = lineup.home_team.get("name", "Hemmalag")
            away_name = lineup.away_team.get("name", "Bortalag")
            
            messagebox.showinfo(
                "Laguppställning hämtad!",
                f"✓ {home_name} vs {away_name}\n\n"
                f"Spelare hämtade:\n"
                f"• {home_name}: {len(lineup.home_team['players'])} spelare\n"
                f"• {away_name}: {len(lineup.away_team['players'])} spelare"
            )
            
            # Save to file
            try:
                filepath = self.data_manager.save_to_file()
                messagebox.showinfo("Sparat", f"Laguppställning sparad till:\n{filepath}")
            except Exception as e:
                messagebox.showwarning("Varning", f"Kunde inte spara:\n{e}")
            
            self.result = self.data_manager.lineup_data
            self.destroy()
            
        except Exception as e:
            try:
                loading.destroy()
            except:
                pass
            
            error_msg = str(e)
            if "Network error" in error_msg or "Name or service not known" in error_msg:
                messagebox.showerror(
                    "Nätverksfel",
                    f"Kunde inte ansluta till API:et.\n\n"
                    f"Kontrollera:\n"
                    f"• Internetanslutning\n"
                    f"• Club ID är korrekt: '{club_id}'\n\n"
                    f"Tekniskt fel: {e}"
                )
            else:
                messagebox.showerror("API-fel", f"Kunde inte hämta från API:\n\n{e}")
    
    def _load_from_swehockey(self):
        """Load lineup from SweHockey using Match ID"""
        match_id = self.match_id_entry.get().strip()
        
        if not match_id:
            messagebox.showwarning("Ogiltigt Match-ID", "Ange ett Match-ID (t.ex. '1010654')")
            return
        
        try:
            # Show loading message
            loading = tk.Toplevel(self)
            loading.title("Hämtar från SweHockey...")
            loading.geometry("400x150")
            loading.transient(self)
            loading.grab_set()
            
            status_label = tk.Label(
                loading,
                text="Hämtar från stats.swehockey.se...",
                font=("Segoe UI", 11)
            )
            status_label.pack(pady=30)
            
            loading.update()
            
            # Scrape SweHockey
            scraper = SweHockeyScraper()
            lineup_data = scraper.scrape_lineup(match_id)
            
            loading.destroy()
            
            # Show preview dialog
            self._show_preview_and_accept(
                lineup_data,
                source_info=f"SweHockey (Match {match_id})",
                reload_callback=lambda: self._load_from_swehockey()
            )
            
        except SweHockeyScraperError as e:
            try:
                loading.destroy()
            except:
                pass
            
            messagebox.showerror(
                "SweHockey-fel",
                f"Kunde inte hämta från SweHockey:\n\n{e}\n\n"
                f"Kontrollera:\n"
                f"• Match-ID är korrekt: '{match_id}'\n"
                f"• Internetanslutning fungerar"
            )
        except Exception as e:
            try:
                loading.destroy()
            except:
                pass
            
            messagebox.showerror("Fel", f"Ett oväntat fel uppstod:\n\n{e}")
    
    def _browse_file(self):
        """Browse for lineup file"""
        filepath = filedialog.askopenfilename(
            title="Välj laguppställningsfil",
            filetypes=[
                ("Excel files", "*.xlsx"),
                ("CSV files", "*.csv"),
                ("JSON files", "*.json"),
                ("All files", "*.*")
            ]
        )
        
        if filepath:
            self._load_from_file(filepath)
    
    def _load_selected_file(self):
        """Load selected file from listbox"""
        selection = self.file_listbox.curselection()
        if not selection:
            messagebox.showwarning("Ingen fil vald", "Välj en fil från listan eller bläddra")
            return
        
        filepath = self.file_listbox.get(selection[0])
        self._load_from_file(filepath)
    
    def _load_from_file(self, filepath: str):
        """Load lineup from file (Excel/CSV/JSON)"""
        if not os.path.exists(filepath):
            messagebox.showerror("Fil saknas", f"Filen finns inte:\n{filepath}")
            return
        
        try:
            # Show loading message
            loading = tk.Toplevel(self)
            loading.title("Läser fil...")
            loading.geometry("400x150")
            loading.transient(self)
            loading.grab_set()
            
            status_label = tk.Label(
                loading,
                text=f"Läser {os.path.basename(filepath)}...",
                font=("Segoe UI", 11)
            )
            status_label.pack(pady=30)
            
            loading.update()
            
            # Parse file
            lineup_data = LineupParsers.parse_file(filepath)
            
            loading.destroy()
            
            # Show preview dialog
            filename = os.path.basename(filepath)
            self._show_preview_and_accept(
                lineup_data,
                source_info=f"Fil: {filename}",
                reload_callback=lambda: self._load_from_file(filepath)
            )
            
        except LineupParseError as e:
            try:
                loading.destroy()
            except:
                pass
            
            messagebox.showerror(
                "Fel vid läsning",
                f"Kunde inte läsa filen:\n\n{e}\n\n"
                f"Kontrollera att filen har rätt format."
            )
        except Exception as e:
            try:
                loading.destroy()
            except:
                pass
            
            messagebox.showerror("Fel", f"Ett oväntat fel uppstod:\n\n{e}")
    
    def _show_preview_and_accept(self, lineup_data: dict, source_info: str = "", reload_callback=None):
        """
        Show preview dialog and handle accept/reload/cancel
        
        Args:
            lineup_data: Dict with 'home' and 'away' keys
            source_info: Source description
            reload_callback: Function to call if user wants to reload
        """
        while True:
            preview = LineupPreviewDialog(self, lineup_data, source_info)
            self.wait_window(preview)
            
            if preview.result == 'accept':
                # User accepted - save to data_manager
                self._accept_lineup_data(lineup_data)
                break
            elif preview.result == 'reload':
                # User wants to reload
                if reload_callback:
                    reload_callback()
                break
            else:
                # User cancelled
                break
    
    def _accept_lineup_data(self, lineup_data: dict):
        """Accept lineup data and close dialog"""
        try:
            # Convert to LineupData format
            from core.data_source import LineupData
            
            lineup_obj = LineupData()
            
            # Home team
            home = lineup_data.get('home', {})
            lineup_obj.home_team = {
                "name": home.get('team_name', ''),
                "logo": "",
                "players": home.get('players', []),
                "staff": home.get('staff', [])
            }
            
            # Away team
            away = lineup_data.get('away', {})
            lineup_obj.away_team = {
                "name": away.get('team_name', ''),
                "logo": "",
                "players": away.get('players', []),
                "staff": away.get('staff', [])
            }
            
            # Metadata
            lineup_obj.metadata = {
                "created": datetime.now().isoformat(),
                "source": "swehockey",  # or detect from source_info
                "match_info": ""
            }
            
            # Save to data_manager
            self.data_manager.lineup_data = lineup_obj
            
            # Show success message
            home_name = lineup_obj.home_team['name']
            away_name = lineup_obj.away_team['name']
            home_players = len(lineup_obj.home_team['players'])
            away_players = len(lineup_obj.away_team['players'])
            
            messagebox.showinfo(
                "Laguppställning godkänd!",
                f"✓ {home_name} vs {away_name}\n\n"
                f"Spelare:\n"
                f"• {home_name}: {home_players} spelare\n"
                f"• {away_name}: {away_players} spelare\n\n"
                f"Laguppställningen är nu laddad och redo att använda!"
            )
            
            # Set result and close
            self.result = lineup_obj
            self.destroy()
            
        except Exception as e:
            messagebox.showerror("Fel", f"Kunde inte spara laguppställning:\n\n{e}")



class EditLineupDialog(tk.Toplevel):
    """
    Dialog for editing lineup data.
    Allows adding staff members to teams.
    """
    
    def __init__(self, parent, data_manager, from_vmix=False):
        super().__init__(parent)
        self.data_manager = data_manager
        self.from_vmix = from_vmix
        self.result = False
        
        self.title("Redigera laguppställning")
        self.geometry("700x600")
        
        self.transient(parent)
        self.grab_set()
        
        self._build()
    
    def _build(self):
        # Title
        if self.from_vmix:
            title_text = "Laguppställning hämtad från vMix"
            subtitle = "Lägg till ledare/tränare för varje lag:"
        else:
            title_text = "Redigera laguppställning"
            subtitle = "Lägg till ledare/tränare:"
        
        tk.Label(
            self,
            text=title_text,
            font=("Segoe UI", 14, "bold")
        ).pack(pady=10)
        
        tk.Label(
            self,
            text=subtitle,
            font=("Segoe UI", 10)
        ).pack(pady=(0, 10))
        
        # Notebook for home/away
        notebook = ttk.Notebook(self)
        notebook.pack(fill=tk.BOTH, expand=True, padx=20, pady=10)
        
        # Home team tab
        home_frame = tk.Frame(notebook, bg="white")
        notebook.add(home_frame, text="HEMMALAG")
        self._build_team_editor(home_frame, "home")
        
        # Away team tab
        away_frame = tk.Frame(notebook, bg="white")
        notebook.add(away_frame, text="BORTALAG")
        self._build_team_editor(away_frame, "away")
        
        # Buttons
        btn_frame = tk.Frame(self)
        btn_frame.pack(fill=tk.X, padx=20, pady=20)
        
        tk.Button(
            btn_frame,
            text="SPARA & FORTSÄTT",
            font=("Segoe UI", 11, "bold"),
            command=self._on_save,
            bg="#2ecc71",
            fg="white",
            width=20,
            height=2
        ).pack(side=tk.RIGHT, padx=5)
        
        tk.Button(
            btn_frame,
            text="AVBRYT",
            font=("Segoe UI", 11),
            command=self.destroy,
            bg="#95a5a6",
            fg="white",
            width=15,
            height=2
        ).pack(side=tk.RIGHT, padx=5)
    
    def _build_team_editor(self, parent, side: str):
        """Build editor for one team"""
        # Team name
        info_frame = tk.Frame(parent, bg="white")
        info_frame.pack(fill=tk.X, padx=10, pady=10)
        
        team_name = self.data_manager.get_team_name(side)
        tk.Label(
            info_frame,
            text=f"Lag: {team_name or '(Inget namn)'}",
            font=("Segoe UI", 12, "bold"),
            bg="white"
        ).pack(anchor=tk.W)
        
        # Player count
        players = self.data_manager.get_players(side)
        tk.Label(
            info_frame,
            text=f"Spelare: {len(players)}",
            font=("Segoe UI", 10),
            bg="white",
            fg="#7f8c8d"
        ).pack(anchor=tk.W)
        
        # Staff section
        tk.Label(
            parent,
            text="Ledare:",
            font=("Segoe UI", 11, "bold"),
            bg="white"
        ).pack(anchor=tk.W, padx=10, pady=(10, 5))
        
        # Staff listbox
        list_frame = tk.Frame(parent, bg="white")
        list_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=5)
        
        scrollbar = tk.Scrollbar(list_frame)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        
        staff_listbox = tk.Listbox(
            list_frame,
            height=8,
            font=("Segoe UI", 10),
            yscrollcommand=scrollbar.set
        )
        staff_listbox.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar.config(command=staff_listbox.yview)
        
        # Populate existing staff
        staff = self.data_manager.get_staff(side)
        for member in staff:
            display = f"{member['role']}: {member['name']}"
            staff_listbox.insert(tk.END, display)
        
        # Store reference
        if side == "home":
            self.home_staff_listbox = staff_listbox
        else:
            self.away_staff_listbox = staff_listbox
        
        # Add staff button
        add_frame = tk.Frame(parent, bg="white")
        add_frame.pack(fill=tk.X, padx=10, pady=10)
        
        tk.Button(
            add_frame,
            text="+ LÄGG TILL LEDARE",
            font=("Segoe UI", 9, "bold"),
            command=lambda: self._add_staff(side),
            bg="#3498db",
            fg="white",
            width=20
        ).pack(side=tk.LEFT, padx=5)
        
        tk.Button(
            add_frame,
            text="TA BORT VALD",
            font=("Segoe UI", 9),
            command=lambda: self._remove_staff(side),
            bg="#e74c3c",
            fg="white",
            width=15
        ).pack(side=tk.LEFT, padx=5)
    
    def _add_staff(self, side: str):
        """Add staff member"""
        dialog = AddStaffDialog(self)
        self.wait_window(dialog)
        
        if dialog.result:
            role, name = dialog.result
            self.data_manager.add_staff_member(side, role, name)
            
            # Update listbox
            listbox = self.home_staff_listbox if side == "home" else self.away_staff_listbox
            display = f"{role}: {name}"
            listbox.insert(tk.END, display)
    
    def _remove_staff(self, side: str):
        """Remove selected staff member"""
        listbox = self.home_staff_listbox if side == "home" else self.away_staff_listbox
        sel = listbox.curselection()
        
        if not sel:
            messagebox.showwarning("Ingen vald", "Välj en ledare att ta bort")
            return
        
        idx = sel[0]
        
        # Remove from data
        staff_list = self.data_manager.lineup_data.home_team["staff"] if side == "home" \
                     else self.data_manager.lineup_data.away_team["staff"]
        if idx < len(staff_list):
            del staff_list[idx]
        
        # Update listbox
        listbox.delete(idx)
    
    def _on_save(self):
        """Save and close"""
        self.result = True
        self.destroy()


class AddStaffDialog(tk.Toplevel):
    """Simple dialog to add a staff member"""
    
    def __init__(self, parent):
        super().__init__(parent)
        self.result = None
        
        self.title("Lägg till ledare")
        self.geometry("400x250")
        self.resizable(False, False)
        
        self.transient(parent)
        self.grab_set()
        
        self._build()
    
    def _build(self):
        tk.Label(
            self,
            text="Lägg till ledare",
            font=("Segoe UI", 12, "bold")
        ).pack(pady=15)
        
        # Role selection
        tk.Label(
            self,
            text="Roll:",
            font=("Segoe UI", 10)
        ).pack(anchor=tk.W, padx=20, pady=(10, 0))
        
        self.role_var = tk.StringVar(value="Huvudtränare")
        role_combo = ttk.Combobox(
            self,
            textvariable=self.role_var,
            values=["Huvudtränare", "Assisterande tränare", "Materialare", "Läkare", "Annat"],
            font=("Segoe UI", 10),
            state="readonly"
        )
        role_combo.pack(fill=tk.X, padx=20, pady=5)
        
        # Name entry
        tk.Label(
            self,
            text="Namn:",
            font=("Segoe UI", 10)
        ).pack(anchor=tk.W, padx=20, pady=(10, 0))
        
        self.name_entry = tk.Entry(
            self,
            font=("Segoe UI", 10)
        )
        self.name_entry.pack(fill=tk.X, padx=20, pady=5)
        self.name_entry.focus()
        
        # Buttons
        btn_frame = tk.Frame(self)
        btn_frame.pack(pady=20)
        
        tk.Button(
            btn_frame,
            text="LÄGG TILL",
            font=("Segoe UI", 10, "bold"),
            command=self._on_ok,
            bg="#2ecc71",
            fg="white",
            width=12
        ).grid(row=0, column=0, padx=5)
        
        tk.Button(
            btn_frame,
            text="AVBRYT",
            font=("Segoe UI", 10),
            command=self.destroy,
            bg="#95a5a6",
            fg="white",
            width=12
        ).grid(row=0, column=1, padx=5)
        
        # Bind Enter key
        self.name_entry.bind("<Return>", lambda e: self._on_ok())
    
    def _on_ok(self):
        """Add staff member"""
        role = self.role_var.get().strip()
        name = self.name_entry.get().strip()
        
        if not name:
            messagebox.showwarning("Ogiltigt namn", "Ange ett namn")
            return
        
        self.result = (role, name)
        self.destroy()

    def _load_from_api_smart(self):
        """Load lineup from API using Club ID (SMART MODE)"""
        club_id = self.club_id_entry.get().strip()
        
        if not club_id:
            messagebox.showwarning("Ogiltigt Club ID", "Ange ett Club ID (t.ex. 'demo')")
            return
        
        try:
            # Show loading message
            loading = tk.Toplevel(self)
            loading.title("Hämtar från API...")
            loading.geometry("400x150")
            loading.transient(self)
            loading.grab_set()
            
            status_label = tk.Label(
                loading,
                text="Ansluter till API...",
                font=("Segoe UI", 11)
            )
            status_label.pack(pady=30)
            
            loading.update()
            
            # Step 1: Fetch lineup directly with Club ID
            status_label.config(text=f"Hämtar laguppställning för {club_id}...")
            loading.update()
            
            lineup_url = f"https://vmix-new.hockeyettan.se/api/lineup/{club_id}"
            players_url = f"https://vmix-new.hockeyettan.se/api/players/{club_id}"  # Not used but kept for compatibility
            
            print(f"Fetching from Club ID: {club_id}")
            lineup = self.data_manager.load_from_api(lineup_url, players_url)
            
            loading.destroy()
            
            # Show success message with team names
            home_name = lineup.home_team.get("name", "Hemmalag")
            away_name = lineup.away_team.get("name", "Bortalag")
            
            messagebox.showinfo(
                "Laguppställning hämtad!",
                f"✓ {home_name} vs {away_name}\n\n"
                f"Spelare hämtade:\n"
                f"• {home_name}: {len(lineup.home_team['players'])} spelare\n"
                f"• {away_name}: {len(lineup.away_team['players'])} spelare\n\n"
                "Du kan nu lägga till ledare/tränare om du vill."
            )
            
            # Show edit dialog to add/edit staff
            edit_dialog = EditLineupDialog(self, self.data_manager, from_vmix=False)
            self.wait_window(edit_dialog)
            
            if edit_dialog.result:
                # Save to file
                try:
                    filepath = self.data_manager.save_to_file()
                    messagebox.showinfo(
                        "Laguppställning sparad",
                        f"Laguppställning har sparats till:\n{filepath}\n\n"
                        "Du kan ladda denna fil nästa gång för att slippa hämta från API."
                    )
                except Exception as e:
                    messagebox.showwarning("Varning", f"Kunde inte spara fil:\n{e}")
                
                self.result = self.data_manager.lineup_data
                self.destroy()
            
        except Exception as e:
            try:
                loading.destroy()
            except:
                pass
            
            error_msg = str(e)
            if "Network error" in error_msg or "Name or service not known" in error_msg:
                messagebox.showerror(
                    "Nätverksfel",
                    f"Kunde inte ansluta till API:et.\n\n"
                    f"Kontrollera:\n"
                    f"• Internetanslutning\n"
                    f"• Club ID är korrekt: '{club_id}'\n\n"
                    f"Tekniskt fel: {e}"
                )
            else:
                messagebox.showerror("API-fel", f"Kunde inte hämta från API:\n\n{e}")
