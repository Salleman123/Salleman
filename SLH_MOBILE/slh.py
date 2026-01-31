#!/usr/bin/env python3
# slh.py
"""
Scoreboard Little Helper (SLH) - MOBILE VERSION
Main entry point

Usage:
    python slh.py
"""

import sys
import json
import shutil
from pathlib import Path

from gui.main_window_mobile import MainWindowMobile


def clear_cache():
    """Clear Python cache files (.pyc and __pycache__)"""
    try:
        cache_cleared = False
        
        # Remove __pycache__ directories
        for pycache in Path('.').rglob('__pycache__'):
            shutil.rmtree(pycache)
            cache_cleared = True
        
        # Remove .pyc files
        for pyc in Path('.').rglob('*.pyc'):
            pyc.unlink()
            cache_cleared = True
        
        if cache_cleared:
            print("✓ Cache cleared!")
        
    except Exception as e:
        print(f"Note: Could not clear cache: {e}")


def load_config(config_path: str = "config.json") -> dict:
    """Load configuration file"""
    path = Path(config_path)
    
    if not path.exists():
        print(f"Error: Configuration file not found: {config_path}")
        print("Please create config.json with vMix connection details.")
        sys.exit(1)
    
    try:
        with open(path, 'r', encoding='utf-8') as f:
            config = json.load(f)
        return config
    except json.JSONDecodeError as e:
        print(f"Error: Invalid JSON in config file: {e}")
        sys.exit(1)
    except Exception as e:
        print(f"Error loading config: {e}")
        sys.exit(1)


def main():
    """Main entry point"""
    print("=" * 60)
    print("  Scoreboard Little Helper (SLH)")
    print("  Version 2.6 - Mobilanpassad layout")
    print("=" * 60)
    print()
    
    # Clear cache automatically
    clear_cache()
    print()
    
    # Load configuration
    config = load_config()
    
    # Validate minimum config
    vmix_cfg = config.get("vmix", {})
    if not vmix_cfg.get("host"):
        print("Error: vMix host not configured in config.json")
        sys.exit(1)
    
    sb_cfg = config.get("scoreboard", {})
    if not sb_cfg.get("input"):
        print("Error: Scoreboard input not configured in config.json")
        sys.exit(1)
    
    print(f"vMix Host: {vmix_cfg.get('host')}:{vmix_cfg.get('port', 8088)}")
    print(f"Scoreboard Input: {sb_cfg.get('input')}")
    print()
    print("Starting GUI...")
    print()
    
    # Create and run main window
    app = MainWindowMobile(config)
    app.protocol("WM_DELETE_WINDOW", app.on_closing)
    app.mainloop()


if __name__ == "__main__":
    main()
