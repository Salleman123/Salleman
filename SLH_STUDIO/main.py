#!/usr/bin/env python3
"""
SLH SETUP STUDIO v5.0
Scoreboard Little Helper - Setup & Data Preparation

Förbered allt INNAN sändning:
1. Konfigurera säsong
2. Importera lag
3. Förbered match
4. Editera lineup
5. Exportera till vMix
6. Starta live-appen
"""

import sys
import tkinter as tk
from pathlib import Path
import os

# Make sure we're in the right directory
os.chdir(Path(__file__).parent)

# Add current directory to path
sys.path.insert(0, str(Path(__file__).parent))

# Import from local gui package
from gui.main_window import SetupStudioWindow


def main():
    """Main entry point"""
    print("=" * 60)
    print("  SLH SETUP STUDIO v5.0")
    print("  Scoreboard Little Helper - Setup & Preparation")
    print("=" * 60)
    print()
    
    # Create main window
    root = tk.Tk()
    app = SetupStudioWindow(root)
    
    # Start event loop
    root.mainloop()


if __name__ == '__main__':
    main()
