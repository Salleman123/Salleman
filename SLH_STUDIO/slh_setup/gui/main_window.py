"""
Main Window for SLH Setup Studio
Modern, clean desktop design (1080x720)
"""

import tkinter as tk
from tkinter import ttk, messagebox
from core.data_manager import DataManager
from gui.season_manager import SeasonManagerPanel


class SetupStudioWindow:
    """Main application window"""
    
    def __init__(self, root):
        self.root = root
        self.root.title("SLH Setup Studio v5.0")
        self.root.geometry("1080x720")
        self.root.minsize(900, 600)
        
        # Data manager
        self.data_manager = DataManager()
        
        # Current state
        self.current_step = 0
        self.current_sport = None
        self.current_season = None
        self.current_match = None
        
        # Build UI
        self._setup_styles()
        self._build_ui()
        
        # Show first step
        self._show_step(0)
    
    def _setup_styles(self):
        """Setup modern ttk styles"""
        style = ttk.Style()
        style.theme_use('clam')
        
        # Configure colors
        bg_color = "#f5f5f5"
        sidebar_color = "#2c3e50"
        accent_color = "#3498db"
        
        # Main background
        self.root.configure(bg=bg_color)
        
        # Button styles
        style.configure(
            'Step.TButton',
            font=('Segoe UI', 11),
            padding=15,
            background=sidebar_color,
            foreground='white'
        )
        
        style.map('Step.TButton',
            background=[('active', accent_color)]
        )
        
        style.configure(
            'Nav.TButton',
            font=('Segoe UI', 10, 'bold'),
            padding=10
        )
        
        style.configure(
            'Accent.TButton',
            font=('Segoe UI', 11, 'bold'),
            padding=12,
            background=accent_color
        )
    
    def _build_ui(self):
        """Build main UI layout"""
        # Main container
        container = tk.Frame(self.root, bg="#f5f5f5")
        container.pack(fill=tk.BOTH, expand=True)
        
        # Left sidebar - Step navigation
        self._build_sidebar(container)
        
        # Right content area
        self._build_content_area(container)
        
        # Bottom navigation
        self._build_navigation(container)
    
    def _build_sidebar(self, parent):
        """Build left sidebar with step buttons"""
        sidebar = tk.Frame(parent, bg="#2c3e50", width=200)
        sidebar.pack(side=tk.LEFT, fill=tk.Y)
        sidebar.pack_propagate(False)
        
        # Header
        header = tk.Label(
            sidebar,
            text="SLH SETUP\nSTUDIO",
            font=("Segoe UI", 16, "bold"),
            bg="#2c3e50",
            fg="white",
            pady=20
        )
        header.pack(fill=tk.X)
        
        tk.Label(
            sidebar,
            text="v5.0",
            font=("Segoe UI", 9),
            bg="#2c3e50",
            fg="#95a5a6"
        ).pack()
        
        # Separator
        tk.Frame(sidebar, bg="#34495e", height=2).pack(fill=tk.X, pady=20)
        
        # Step buttons
        self.step_buttons = []
        steps = [
            ("1. SÄSONG", "Konfigurera säsong"),
            ("2. LAG", "Importera lag"),
            ("3. MATCH", "Förbered match"),
            ("4. LINEUP", "Editera lineup"),
            ("5. EXPORT", "Exportera data")
        ]
        
        for i, (title, tooltip) in enumerate(steps):
            btn = tk.Button(
                sidebar,
                text=title,
                font=("Segoe UI", 11, "bold"),
                bg="#34495e",
                fg="white",
                activebackground="#3498db",
                activeforeground="white",
                relief="flat",
                cursor="hand2",
                command=lambda step=i: self._show_step(step),
                pady=15
            )
            btn.pack(fill=tk.X, padx=10, pady=5)
            self.step_buttons.append(btn)
        
        # Footer
        tk.Frame(sidebar, bg="#2c3e50").pack(fill=tk.BOTH, expand=True)
        
        footer = tk.Label(
            sidebar,
            text="© 2025 SLH\nScoreboard Little Helper",
            font=("Segoe UI", 8),
            bg="#2c3e50",
            fg="#7f8c8d",
            pady=10
        )
        footer.pack(side=tk.BOTTOM)
    
    def _build_content_area(self, parent):
        """Build main content area"""
        # Content container with padding
        content_frame = tk.Frame(parent, bg="#f5f5f5")
        content_frame.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=20, pady=20)
        
        # Title area
        title_frame = tk.Frame(content_frame, bg="#f5f5f5")
        title_frame.pack(fill=tk.X, pady=(0, 20))
        
        self.title_label = tk.Label(
            title_frame,
            text="Konfigurera Säsong",
            font=("Segoe UI", 20, "bold"),
            bg="#f5f5f5",
            fg="#2c3e50"
        )
        self.title_label.pack(side=tk.LEFT)
        
        self.subtitle_label = tk.Label(
            title_frame,
            text="Skapa eller välj en säsong",
            font=("Segoe UI", 11),
            bg="#f5f5f5",
            fg="#7f8c8d"
        )
        self.subtitle_label.pack(side=tk.LEFT, padx=15)
        
        # Separator
        tk.Frame(content_frame, bg="#bdc3c7", height=1).pack(fill=tk.X, pady=(0, 20))
        
        # Content panels (will be swapped)
        self.content_container = tk.Frame(content_frame, bg="#f5f5f5")
        self.content_container.pack(fill=tk.BOTH, expand=True)
        
        # Create panels
        self.panels = {}
        self._create_panels()
    
    def _create_panels(self):
        """Create all content panels"""
        # Panel 1: Season Manager
        self.panels[0] = SeasonManagerPanel(
            self.content_container,
            self.data_manager,
            on_season_select=self._on_season_selected
        )
        
        # Panel 2: Team Importer
        from gui.team_importer import TeamImporterPanel
        self.panels[1] = TeamImporterPanel(
            self.content_container,
            self.data_manager,
            current_sport=self.current_sport,
            current_season=self.current_season
        )
        
        # Panels 3-5 will be created as placeholders for now
        for i in range(2, 5):
            panel = tk.Frame(self.content_container, bg="#f5f5f5")
            label = tk.Label(
                panel,
                text=f"Panel {i+1} - Coming soon...",
                font=("Segoe UI", 14),
                bg="#f5f5f5",
                fg="#95a5a6"
            )
            label.pack(expand=True)
            self.panels[i] = panel
    
    def _build_navigation(self, parent):
        """Build bottom navigation bar"""
        nav_frame = tk.Frame(parent, bg="white", height=60)
        nav_frame.pack(side=tk.BOTTOM, fill=tk.X)
        nav_frame.pack_propagate(False)
        
        # Add shadow effect
        tk.Frame(nav_frame, bg="#dcdde1", height=1).pack(fill=tk.X)
        
        # Button container
        btn_container = tk.Frame(nav_frame, bg="white")
        btn_container.pack(fill=tk.BOTH, expand=True, padx=20, pady=10)
        
        # Previous button
        self.prev_btn = tk.Button(
            btn_container,
            text="← Föregående",
            font=("Segoe UI", 10),
            command=self._previous_step,
            bg="white",
            fg="#2c3e50",
            relief="solid",
            bd=1,
            cursor="hand2",
            padx=20,
            pady=8
        )
        self.prev_btn.pack(side=tk.LEFT)
        
        # Next button
        self.next_btn = tk.Button(
            btn_container,
            text="Nästa →",
            font=("Segoe UI", 10, "bold"),
            command=self._next_step,
            bg="#3498db",
            fg="white",
            relief="flat",
            cursor="hand2",
            padx=20,
            pady=8
        )
        self.next_btn.pack(side=tk.RIGHT, padx=10)
        
        # Start SLH button (shown on last step)
        self.start_btn = tk.Button(
            btn_container,
            text="🚀 STARTA SLH",
            font=("Segoe UI", 11, "bold"),
            command=self._start_slh,
            bg="#27ae60",
            fg="white",
            relief="flat",
            cursor="hand2",
            padx=30,
            pady=10
        )
    
    def _show_step(self, step: int):
        """Show specific step"""
        if step < 0 or step >= len(self.panels):
            return
        
        self.current_step = step
        
        # Update sidebar buttons
        for i, btn in enumerate(self.step_buttons):
            if i == step:
                btn.configure(bg="#3498db", fg="white")
            else:
                btn.configure(bg="#34495e", fg="white")
        
        # Update title
        titles = [
            ("Konfigurera Säsong", "Skapa eller välj en säsong"),
            ("Importera Lag", "Hämta lag från API eller SweHockey"),
            ("Förbered Match", "Välj match och grundinformation"),
            ("Editera Lineup", "Granska och editera spelarlista"),
            ("Exportera Data", "Skapa filer för vMix")
        ]
        
        if step < len(titles):
            self.title_label.configure(text=titles[step][0])
            self.subtitle_label.configure(text=titles[step][1])
        
        # Hide all panels
        for panel in self.panels.values():
            panel.pack_forget()
        
        # Show current panel
        if step in self.panels:
            self.panels[step].pack(fill=tk.BOTH, expand=True)
        
        # Update navigation buttons
        self.prev_btn.configure(state=tk.NORMAL if step > 0 else tk.DISABLED)
        self.next_btn.configure(state=tk.NORMAL if step < len(self.panels) - 1 else tk.DISABLED)
        
        # Show/hide start button on last step
        if step == len(self.panels) - 1:
            self.next_btn.pack_forget()
            self.start_btn.pack(side=tk.RIGHT, padx=10)
        else:
            self.start_btn.pack_forget()
            self.next_btn.pack(side=tk.RIGHT, padx=10)
    
    def _previous_step(self):
        """Go to previous step"""
        if self.current_step > 0:
            self._show_step(self.current_step - 1)
    
    def _next_step(self):
        """Go to next step"""
        if self.current_step < len(self.panels) - 1:
            self._show_step(self.current_step + 1)
    
    def _on_season_selected(self, sport: str, year: str):
        """Callback when season is selected"""
        self.current_sport = sport
        self.current_season = year
        
        # Update Team Importer panel
        if 1 in self.panels and hasattr(self.panels[1], 'set_season'):
            self.panels[1].set_season(sport, year)
        
        print(f"Selected: {sport} {year}")
    
    def _start_slh(self):
        """Start the live SLH app"""
        result = messagebox.askyesno(
            "Starta SLH",
            "Allt är klart!\n\nVill du starta SLH Live-appen nu?",
            icon='question'
        )
        
        if result:
            messagebox.showinfo("Info", "SLH Live kommer att startas...\n(Integration kommer i v5.1)")
