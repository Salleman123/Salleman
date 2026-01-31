# gui/api_lineup_dialog.py
"""Dialog for importing lineup from Hockeyettan API"""

import tkinter as tk
from tkinter import messagebox, ttk


class ApiLineupDialog(tk.Toplevel):
    """Dialog for fetching lineup from Hockeyettan API using ClubIds"""
    
    def __init__(self, parent, data_manager):
        super().__init__(parent)
        self.data_manager = data_manager
        self.result = None
        
        self.title("Hämta från Hockeyettan API")
        self.geometry("500x350")
        self.resizable(False, False)
        
        # Center on parent
        self.transient(parent)
        self.grab_set()
        
        self._build()
    
    def _build(self):
        """Build dialog UI"""
        # Header
        header = tk.Label(
            self,
            text="Hämta laguppställning från Hockeyettan API",
            font=("Segoe UI", 12, "bold"),
            bg="#2c3e50",
            fg="white",
            pady=10
        )
        header.pack(fill=tk.X)
        
        # Content frame
        content = tk.Frame(self, bg="#ecf0f1")
        content.pack(fill=tk.BOTH, expand=True, padx=20, pady=20)
        
        # Info text
        info_text = ("Ange Match ID för matchen.\n"
                     "Match ID finns i URL:en på stats.swehockey.se\n"
                     "Exempel: 1009915 för Lindlövens IF vs Piteå HC")
        
        tk.Label(
            content,
            text=info_text,
            font=("Segoe UI", 9),
            bg="#ecf0f1",
            fg="#555",
            justify=tk.LEFT
        ).pack(pady=(0, 20))
        
        # Match ID
        match_frame = tk.LabelFrame(
            content,
            text="MATCH",
            font=("Segoe UI", 10, "bold"),
            bg="#ecf0f1",
            pady=10
        )
        match_frame.pack(fill=tk.X, pady=5)
        
        tk.Label(
            match_frame,
            text="Match ID:",
            font=("Segoe UI", 10),
            bg="#ecf0f1"
        ).pack(side=tk.LEFT, padx=10)
        
        self.match_id = tk.Entry(match_frame, width=20, font=("Segoe UI", 10))
        self.match_id.insert(0, "1009915")  # Example
        self.match_id.pack(side=tk.LEFT, padx=5)
        
        # Buttons
        btn_frame = tk.Frame(content, bg="#ecf0f1")
        btn_frame.pack(pady=20)
        
        tk.Button(
            btn_frame,
            text="Hämta lineup",
            width=15,
            font=("Segoe UI", 10, "bold"),
            command=self._on_fetch,
            bg="#4CAF50",
            fg="white",
            relief="raised",
            bd=2
        ).pack(side=tk.LEFT, padx=5)
        
        tk.Button(
            btn_frame,
            text="Avbryt",
            width=15,
            font=("Segoe UI", 10),
            command=self.destroy
        ).pack(side=tk.LEFT, padx=5)
    
    def _on_fetch(self):
        """Fetch lineup from API using MatchId"""
        match_id = self.match_id.get().strip()
        
        if not match_id:
            messagebox.showerror("Fel", "Ange Match ID")
            return
        
        # Validate numeric
        if not match_id.isdigit():
            messagebox.showerror("Fel", "Match ID måste vara ett nummer")
            return
        
        try:
            # Build URL
            base_url = "https://vmix-new.hockeyettan.se/api"
            lineup_url = f"{base_url}/lineup/{match_id}"
            
            # Show progress
            progress = tk.Toplevel(self)
            progress.title("Hämtar...")
            progress.geometry("300x100")
            progress.transient(self)
            tk.Label(
                progress,
                text="Hämtar lineup från API...",
                font=("Segoe UI", 10)
            ).pack(pady=30)
            progress.update()
            
            # Fetch data
            lineup_data = self.data_manager.load_from_api_lineup(lineup_url)
            
            progress.destroy()
            
            self.result = lineup_data
            self.destroy()
            
        except Exception as e:
            if 'progress' in locals():
                progress.destroy()
            messagebox.showerror("API-fel", f"Kunde inte hämta lineup:\n{str(e)}")
