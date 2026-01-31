# core/json_exporter.py
"""
JSON Exporter for vMix-compatible format
Exports lineup data in the exact same format as Hockeyettan API
"""

import json
from typing import Dict, List, Any
from pathlib import Path


class JSONExporter:
    """
    Export lineup data to JSON files in vMix-compatible format
    """
    
    def __init__(self, lineup_state):
        """
        Args:
            lineup_state: LineupState instance with current data
        """
        self.lineup = lineup_state
    
    def export_lineup_json(self, filepath: str) -> str:
        """
        Export complete lineup to JSON (exact API format)
        
        Args:
            filepath: Path to save JSON file
            
        Returns:
            Success message
        """
        if not self.lineup.has_data():
            raise ValueError("No lineup data to export")
        
        # Get data
        home = self.lineup.home_team
        away = self.lineup.away_team
        
        # Build JSON in exact API format
        data = {
            # Away team
            "A_TeamName.Text": away.get('name', ''),
            "A_TeamLogo.Source": away.get('logo', ''),
            "A_A_LogoTeam.Source": away.get('logo', ''),
            
            # Home team
            "H_TeamName.Text": home.get('name', ''),
            "H_TeamLogo.Source": home.get('logo', ''),
            "H_LogoTeam.Source": home.get('logo', ''),
            
            # Headers (static)
            "HeadlineGoalies.Text": "MÅLVAKTER",
            "HeadlineDef.Text": "BACKPAR",
            "HeadlineForw.Text": "FORWARDS",
            
            # Backgrounds (static)
            "BG.Source": "https://vmix-new.hockeyettan.se/scoreImages/lineupBG.png",
            "Divider1.Source": "https://vmix-new.hockeyettan.se/tableImages/lineup-DIVISION.png",
            "Divider2.Source": "https://vmix-new.hockeyettan.se/tableImages/lineup-DIVISION.png",
            "Divider3.Source": "https://vmix-new.hockeyettan.se/tableImages/lineup-DIVISION.png",
        }
        
        # Add home players
        home_players = home.get('players', [])
        self._add_team_players(data, home_players, 'H_')
        
        # Add away players
        away_players = away.get('players', [])
        self._add_team_players(data, away_players, 'A_')
        
        # Wrap in array (API returns array with single object)
        output = [data]
        
        # Save to file
        Path(filepath).parent.mkdir(parents=True, exist_ok=True)
        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(output, f, indent=2, ensure_ascii=False)
        
        return f"✓ Exported lineup to {Path(filepath).name}"
    
    def _add_team_players(self, data: Dict, players: List[Dict], prefix: str):
        """
        Add players to data dict in vMix format
        
        Args:
            data: Data dict to add to
            players: List of player dicts
            prefix: Team prefix (H_ or A_)
        """
        # Categorize players by position
        goalies = []
        defenders = []
        forwards = []
        
        for player in players:
            pos = player.get('position', 'F').upper()
            if pos in ['G', 'GK']:
                goalies.append(player)
            elif pos in ['D', 'LD', 'RD']:
                defenders.append(player)
            else:
                forwards.append(player)
        
        # Add goalies (GK1, GK2)
        for i, gk in enumerate(goalies[:2], 1):
            data[f"{prefix}GK{i}_name.Text"] = gk.get('name', '').upper()
            data[f"{prefix}GK{i}_number.Text"] = gk.get('number', '')
            data[f"{prefix}GK{i}_plate.Source"] = "https://vmix-new.hockeyettan.se/scoreImages/lineup-PLATE.png"
            data[f"{prefix}GK{i}_picture.Source"] = "https://vmix-new.hockeyettan.se/Players/empty2.png"
        
        # Fill empty goalie slots
        for i in range(len(goalies[:2]) + 1, 3):
            data[f"{prefix}GK{i}_name.Text"] = ""
            data[f"{prefix}GK{i}_number.Text"] = ""
            data[f"{prefix}GK{i}_plate.Source"] = ""
            data[f"{prefix}GK{i}_picture.Source"] = "https://vmix-new.hockeyettan.se/Players/empty2.png"
        
        # Add defenders (LD1-LD5, RD1-RD5)
        # Split defenders into left/right (alternate)
        left_d = defenders[0::2]  # Even indices
        right_d = defenders[1::2]  # Odd indices
        
        for i, ld in enumerate(left_d[:5], 1):
            data[f"{prefix}LD{i}_name.Text"] = ld.get('name', '').upper()
            data[f"{prefix}LD{i}_number.Text"] = ld.get('number', '')
            data[f"{prefix}LD{i}_plate.Source"] = "https://vmix-new.hockeyettan.se/scoreImages/lineup-PLATE.png"
            data[f"{prefix}LD{i}_picture.Source"] = "https://vmix-new.hockeyettan.se/Players/empty2.png"
        
        for i in range(len(left_d[:5]) + 1, 6):
            data[f"{prefix}LD{i}_name.Text"] = ""
            data[f"{prefix}LD{i}_number.Text"] = ""
            data[f"{prefix}LD{i}_plate.Source"] = ""
            data[f"{prefix}LD{i}_picture.Source"] = "https://vmix-new.hockeyettan.se/Players/empty2.png"
        
        for i, rd in enumerate(right_d[:5], 1):
            data[f"{prefix}RD{i}_name.Text"] = rd.get('name', '').upper()
            data[f"{prefix}RD{i}_number.Text"] = rd.get('number', '')
            data[f"{prefix}RD{i}_plate.Source"] = "https://vmix-new.hockeyettan.se/scoreImages/lineup-PLATE.png"
            data[f"{prefix}RD{i}_picture.Source"] = "https://vmix-new.hockeyettan.se/Players/empty2.png"
        
        for i in range(len(right_d[:5]) + 1, 6):
            data[f"{prefix}RD{i}_name.Text"] = ""
            data[f"{prefix}RD{i}_number.Text"] = ""
            data[f"{prefix}RD{i}_plate.Source"] = ""
            data[f"{prefix}RD{i}_picture.Source"] = "https://vmix-new.hockeyettan.se/Players/empty2.png"
        
        # Add forwards (LW1-LW5, C1-C5, RW1-RW5)
        # Split into thirds
        third = len(forwards) // 3
        left_w = forwards[0:third]
        center = forwards[third:third*2]
        right_w = forwards[third*2:]
        
        for i, lw in enumerate(left_w[:5], 1):
            data[f"{prefix}LW{i}_name.Text"] = lw.get('name', '').upper()
            data[f"{prefix}LW{i}_number.Text"] = lw.get('number', '')
            data[f"{prefix}LW{i}_plate.Source"] = "https://vmix-new.hockeyettan.se/scoreImages/lineup-PLATE.png"
            data[f"{prefix}LW{i}_picture.Source"] = "https://vmix-new.hockeyettan.se/Players/empty2.png"
        
        for i in range(len(left_w[:5]) + 1, 6):
            data[f"{prefix}LW{i}_name.Text"] = ""
            data[f"{prefix}LW{i}_number.Text"] = ""
            data[f"{prefix}LW{i}_plate.Source"] = ""
            data[f"{prefix}LW{i}_picture.Source"] = "https://vmix-new.hockeyettan.se/Players/empty2.png"
        
        for i, c in enumerate(center[:5], 1):
            data[f"{prefix}C{i}_name.Text"] = c.get('name', '').upper()
            data[f"{prefix}C{i}_number.Text"] = c.get('number', '')
            data[f"{prefix}C{i}_plate.Source"] = "https://vmix-new.hockeyettan.se/scoreImages/lineup-PLATE.png"
            data[f"{prefix}C{i}_picture.Source"] = "https://vmix-new.hockeyettan.se/Players/empty2.png"
        
        for i in range(len(center[:5]) + 1, 6):
            data[f"{prefix}C{i}_name.Text"] = ""
            data[f"{prefix}C{i}_number.Text"] = ""
            data[f"{prefix}C{i}_plate.Source"] = ""
            data[f"{prefix}C{i}_picture.Source"] = "https://vmix-new.hockeyettan.se/Players/empty2.png"
        
        for i, rw in enumerate(right_w[:5], 1):
            data[f"{prefix}RW{i}_name.Text"] = rw.get('name', '').upper()
            data[f"{prefix}RW{i}_number.Text"] = rw.get('number', '')
            data[f"{prefix}RW{i}_plate.Source"] = "https://vmix-new.hockeyettan.se/scoreImages/lineup-PLATE.png"
            data[f"{prefix}RW{i}_picture.Source"] = "https://vmix-new.hockeyettan.se/Players/empty2.png"
        
        for i in range(len(right_w[:5]) + 1, 6):
            data[f"{prefix}RW{i}_name.Text"] = ""
            data[f"{prefix}RW{i}_number.Text"] = ""
            data[f"{prefix}RW{i}_plate.Source"] = ""
            data[f"{prefix}RW{i}_picture.Source"] = "https://vmix-new.hockeyettan.se/Players/empty2.png"
        
        # Extra defenders (XD1-XD5) - usually empty
        for i in range(1, 6):
            data[f"{prefix}XD{i}_name.Text"] = ""
            data[f"{prefix}XD{i}_number.Text"] = ""
            data[f"{prefix}XD{i}_plate.Source"] = ""
            data[f"{prefix}XD{i}_picture.Source"] = "https://vmix-new.hockeyettan.se/Players/empty2.png"
    
    def export_scoreboard_json(self, filepath: str) -> str:
        """
        Export scoreboard data (minimal - just logos and names from SLH)
        
        Args:
            filepath: Path to save JSON file
            
        Returns:
            Success message
        """
        if not self.lineup.has_data():
            raise ValueError("No lineup data to export")
        
        # Get data
        home = self.lineup.home_team
        away = self.lineup.away_team
        
        # Build minimal scoreboard (SLH only provides these fields)
        data = {
            "HomeName.Text": home.get('name', ''),
            "AwayName.Text": away.get('name', ''),
            "HomeLogo.Source": home.get('logo', ''),
            "AwayLogo.Source": away.get('logo', ''),
            
            # These will be updated by SLH or OCR
            "HomeScore.Text": 0,
            "AwayScore.Text": 0,
            "Time.Text": "{0:20:00|mm:ss}",
            "PeriodNr.Text": 1,
            "PeriodText.Text": "PERIOD",
            
            # Empty penalties
            "HomeP1time.Text": "00:00",
            "HomeP2time.Text": "00:00",
            "AwayP1time.Text": "00:00",
            "AwayP2time.Text": "00:00",
            
            # Static images
            "HomeP1bg.Source": "https://vmix-new.hockeyettan.se/scoreImages/utvisningsskylt.png",
            "HomeP2bg.Source": "https://vmix-new.hockeyettan.se/scoreImages/utvisningsskylt.png",
            "AwayP1bg.Source": "https://vmix-new.hockeyettan.se/scoreImages/utvisningsskylt.png",
            "AwayP2bg.Source": "https://vmix-new.hockeyettan.se/scoreImages/utvisningsskylt.png",
            "PeriodSkylt.Source": "https://vmix-new.hockeyettan.se/scoreImages/periodskylt.png",
            "BG.Source": "https://vmix-new.hockeyettan.se/premagesLogo/topBG.png"
        }
        
        # Wrap in array
        output = [data]
        
        # Save to file
        Path(filepath).parent.mkdir(parents=True, exist_ok=True)
        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(output, f, indent=2, ensure_ascii=False)
        
        return f"✓ Exported scoreboard to {Path(filepath).name}"
    
    def export_match_json(self, filepath: str) -> str:
        """
        Export match stats (minimal - SLH only has basic info)
        
        Args:
            filepath: Path to save JSON file
            
        Returns:
            Success message
        """
        if not self.lineup.has_data():
            raise ValueError("No lineup data to export")
        
        # Get data
        home = self.lineup.home_team
        away = self.lineup.away_team
        
        # Build minimal match data (SLH only provides team info)
        data = {
            "TeamNameHome.Text": home.get('name', ''),
            "TeamNameAway.Text": away.get('name', ''),
            "HomeName.Text": home.get('name', ''),
            "AwayName.Text": away.get('name', ''),
            "LogoHome.Source": home.get('logo', ''),
            "LogoAway.Source": away.get('logo', ''),
            "HomeLogo.Source": home.get('logo', ''),
            "AwayLogo.Source": away.get('logo', ''),
            
            # Placeholders for stats (would come from API during game)
            "HomeScore.Text": 0,
            "AwayScore.Text": 0,
            "Time.Text": "{0:20:00|mm:ss}",
            "StatsHomeGoals.Text": 0,
            "StatsAwayGoals.Text": 0,
            "StatsHomeShots.Text": "0 (0, 0, 0)",
            "StatsAwayShots.Text": "0 (0, 0, 0)",
            "StatsHomeSav.Text": 0,
            "StatsAwaySav.Text": 0,
            "StatsHomePP.Text": "0%",
            "StatsAwayPP.Text": "0%",
            "StatsHomePen.Text": "0 min",
            "StatsAwayPen.Text": "0 min",
            
            # Static
            "Headline.Text": "MATCHSTATISTIK",
            "pre_Headline.Text": "MATCHSTART",
            "HeadlineGoals.Text": "MÅL",
            "HeadlineShots.Text": "SKOTT",
            "HeadlineSav.Text": "RÄDDNINGAR",
            "HeadlinePP.Text": "POWERPLAY",
            "HeadlinePen.Text": "UTVISNINGAR",
            "Textrad1.Text": "",
            "Textrad2.Text": "",
            "TextBottom.Text": "",
            "ImgBottom.Source": "",
            "DomareNamn1.Text": "",
            "DomareNamn2.Text": "",
            "DomareNamn3.Text": "",
            "DomareTitel1.Text": "REFEREE",
            "DomareTitel2.Text": "LINESMAN",
            "DomareTitel3.Text": "LINESMAN"
        }
        
        # Wrap in array
        output = [data]
        
        # Save to file
        Path(filepath).parent.mkdir(parents=True, exist_ok=True)
        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(output, f, indent=2, ensure_ascii=False)
        
        return f"✓ Exported match to {Path(filepath).name}"
