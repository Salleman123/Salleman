# core/data_source.py
"""
DataSource Manager - handles lineup data locally
Reduces vMix API load by caching lineup information
"""

import json
import os
from typing import Dict, List, Tuple, Optional
from datetime import datetime
from urllib.request import urlopen
from urllib.error import URLError


class LineupData:
    """Container for lineup data"""
    
    def __init__(self):
        self.home_team = {
            "name": "",
            "logo": "",
            "players": [],  # [{"number": "1", "name": "...", "position": ""}]
            "staff": []     # [{"role": "...", "name": ""}]
        }
        self.away_team = {
            "name": "",
            "logo": "",
            "players": [],
            "staff": []
        }
        self.metadata = {
            "created": datetime.now().isoformat(),
            "source": "manual",
            "match_info": ""
        }
    
    def to_dict(self) -> dict:
        """Convert to dictionary for JSON serialization"""
        return {
            "home_team": self.home_team,
            "away_team": self.away_team,
            "metadata": self.metadata
        }
    
    @classmethod
    def from_dict(cls, data: dict):
        """Create LineupData from dictionary"""
        lineup = cls()
        lineup.home_team = data.get("home_team", lineup.home_team)
        lineup.away_team = data.get("away_team", lineup.away_team)
        lineup.metadata = data.get("metadata", lineup.metadata)
        return lineup


class DataSourceManager:
    """
    Manages lineup data from various sources.
    Provides unified interface for accessing player/staff information.
    """
    
    def __init__(self, cache_dir: str = "./lineup_cache"):
        self.cache_dir = cache_dir
        self.lineup_data: Optional[LineupData] = None
        
        # Create cache directory if it doesn't exist
        os.makedirs(cache_dir, exist_ok=True)
    
    # ========================================
    # Load from vMix
    # ========================================
    
    def load_from_vmix(self, vmix_client, config: dict) -> LineupData:
        """
        Load lineup data from vMix inputs.
        Reads LINEUP HEMMA and LINEUP BORTA inputs.
        """
        lineup = LineupData()
        lineup.metadata["source"] = "vmix"
        lineup.metadata["created"] = datetime.now().isoformat()
        
        # Load home team
        home_input = config.get("lineup", {}).get("home_input", "LINEUP HEMMA")
        lineup.home_team["players"] = self._read_lineup_from_vmix(vmix_client, home_input)
        
        # Load away team
        away_input = config.get("lineup", {}).get("away_input", "LINEUP BORTA")
        lineup.away_team["players"] = self._read_lineup_from_vmix(vmix_client, away_input)
        
        # Try to get team names from scoreboard
        try:
            sb_input = config.get("scoreboard", {}).get("input", "")
            sb_num = vmix_client.find_input_number(sb_input)
            if sb_num:
                root = vmix_client.get_status_xml()
                for inp in root.findall("./inputs/input"):
                    if inp.get("number") == sb_num:
                        for txt in inp.findall("./text"):
                            name = txt.get("name", "")
                            if name == config.get("scoreboard", {}).get("home_name_field"):
                                lineup.home_team["short_name"] = (txt.text or "").strip()
                            elif name == config.get("scoreboard", {}).get("away_name_field"):
                                lineup.away_team["short_name"] = (txt.text or "").strip()
        except Exception:
            pass
        
        # Try to get FULL names and BIG logos from SCOREBOARD NERE
        try:
            sb_nere_cfg = config.get("scoreboard_nere", {})
            sb_nere_input = sb_nere_cfg.get("input", "SCOREBOARD NERE")
            sb_nere_num = vmix_client.find_input_number(sb_nere_input)
            if sb_nere_num:
                root = vmix_client.get_status_xml()
                for inp in root.findall("./inputs/input"):
                    if inp.get("number") == sb_nere_num:
                        # Get full names
                        for txt in inp.findall("./text"):
                            name = txt.get("name", "")
                            if name == sb_nere_cfg.get("home_name_field", "HomeName.Text"):
                                lineup.home_team["name"] = (txt.text or "").strip()
                            elif name == sb_nere_cfg.get("away_name_field", "AwayName.Text"):
                                lineup.away_team["name"] = (txt.text or "").strip()
                        
                        # Get logos (both big and small)
                        for img in inp.findall("./image"):
                            name = img.get("name", "")
                            if name == sb_nere_cfg.get("home_logo_big_field", "LogoHome.Source"):
                                lineup.home_team["logo_pregame"] = (img.text or "").strip()
                            elif name == sb_nere_cfg.get("away_logo_big_field", "LogoAway.Source"):
                                lineup.away_team["logo_pregame"] = (img.text or "").strip()
                            elif name == sb_nere_cfg.get("home_logo_small_field", "HomeLogo.Source"):
                                lineup.home_team["logo_teams"] = (img.text or "").strip()
                            elif name == sb_nere_cfg.get("away_logo_small_field", "AwayLogo.Source"):
                                lineup.away_team["logo_teams"] = (img.text or "").strip()
        except Exception as e:
            print(f"Note: Could not read from SCOREBOARD NERE: {e}")
            pass
        
        self.lineup_data = lineup
        return lineup
    
    def _read_lineup_from_vmix(self, vmix_client, input_name: str) -> List[dict]:
        """
        Read player list from vMix input.
        Returns list of {"number": "1", "name": "...", "position": ""}
        """
        if not input_name:
            return []
        
        try:
            root = vmix_client.get_status_xml()
        except Exception:
            return []
        
        # Find lineup input
        for inp in root.findall("./inputs/input"):
            title = (inp.get("title") or "").strip()
            if title == input_name:
                players = []
                
                # Extract player data
                for txt in inp.findall("./text"):
                    name = txt.get("name") or ""
                    if name.endswith("_number.Text"):
                        num = (txt.text or "").strip()
                        base = name.replace("_number.Text", "")
                        
                        # Find corresponding name
                        player_name = ""
                        for n in inp.findall("./text"):
                            if (n.get("name") or "") == base + "_name.Text":
                                player_name = (n.text or "").strip()
                                break
                        
                        # Find position (if exists)
                        position = ""
                        for p in inp.findall("./text"):
                            if (p.get("name") or "") == base + "_position.Text":
                                position = (p.text or "").strip()
                                break
                        
                        if num or player_name:
                            players.append({
                                "number": num,
                                "name": player_name,
                                "position": position
                            })
                
                # Sort by number
                players.sort(key=lambda x: int(x["number"]) if x["number"].isdigit() else 999)
                return players
        
        return []
    
    # ========================================
    # Load from API
    # ========================================
    
    def load_from_api_lineup(self, lineup_url: str) -> LineupData:
        """
        Load lineup from NEW Hockeyettan API (2026 format).
        Uses MatchId-based endpoint that returns BOTH teams in one object.
        Format: Single object with A_ (away) and H_ (home) prefixed fields.
        """
        lineup = LineupData()
        lineup.metadata["source"] = "api_lineup"
        lineup.metadata["created"] = datetime.now().isoformat()
        
        try:
            # Fetch lineup data
            print(f"Fetching lineup from: {lineup_url}")
            with urlopen(lineup_url, timeout=10) as response:
                data = json.loads(response.read().decode('utf-8'))
            
            print(f"Response type: {type(data)}")
            
            # Handle different response formats
            lineup_obj = None
            
            # Check if API returned a string (error message)
            if isinstance(data, str):
                raise RuntimeError(f"API-meddelande: {data}")
            
            if isinstance(data, list):
                print(f"List format: {len(data)} items")
                
                # Check if list contains string (error message)
                if len(data) > 0 and isinstance(data[0], str):
                    raise RuntimeError(f"API-meddelande: {data[0]}")
                
                if len(data) == 0:
                    raise RuntimeError("API returnerade tom lista - kontrollera Match ID")
                
                lineup_obj = data[0]
            elif isinstance(data, dict):
                print("Dict format")
                # Check if error response
                if 'error' in data:
                    raise RuntimeError(f"API-fel: {data.get('error', 'Okänt fel')}")
                lineup_obj = data
            
            if not lineup_obj:
                raise RuntimeError("Ingen data från API - kontrollera Match ID")
            
            if lineup_obj and isinstance(lineup_obj, dict):
                # Check if it's vMix field format (has H_ and A_ prefixes)
                has_vmix_format = any(key.startswith('H_') or key.startswith('A_') for key in lineup_obj.keys())
                
                if has_vmix_format:
                    print("vMix field format detected")
                    # Parse home team (H_ prefix)
                    self._parse_lineup_team(lineup.home_team, lineup_obj, 'H_')
                    
                    # Parse away team (A_ prefix)
                    self._parse_lineup_team(lineup.away_team, lineup_obj, 'A_')
                else:
                    print("Standard format - no data parsed")
                
                print(f"API import: {len(lineup.home_team['players'])} home, {len(lineup.away_team['players'])} away")
            else:
                print(f"Unexpected format: {type(lineup_obj)}")
            
            return lineup
            
        except Exception as e:
            import traceback
            traceback.print_exc()
            raise RuntimeError(f"API fetch failed: {e}")
    
    def _parse_lineup_team(self, team: dict, lineup_obj: dict, prefix: str):
        """
        Parse team from lineup object with H_ or A_ prefix.
        Positions: GK (goalkeeper), LD/RD (defense), LW/C/RW (forwards)
        """
        # Extract team name and logo
        team['name'] = lineup_obj.get(f'{prefix}TeamName.Text', '')
        team['logo'] = lineup_obj.get(f'{prefix}TeamLogo.Source', '')
        
        # Position groups and their codes
        positions = [
            ('GK', 'G', 2),   # Goalkeepers (GK1, GK2)
            ('LD', 'D', 5),   # Left Defense (LD1-LD5)
            ('RD', 'D', 5),   # Right Defense (RD1-RD5)
            ('LW', 'F', 5),   # Left Wing (LW1-LW5)
            ('C', 'F', 5),    # Center (C1-C5)
            ('RW', 'F', 5),   # Right Wing (RW1-RW5)
        ]
        
        for pos_code, position, count in positions:
            for i in range(1, count + 1):
                name_key = f'{prefix}{pos_code}{i}_name.Text'
                number_key = f'{prefix}{pos_code}{i}_number.Text'
                
                name = lineup_obj.get(name_key, '').strip()
                number = lineup_obj.get(number_key, '')
                
                if name and number:
                    team['players'].append({
                        'number': str(number),
                        'name': name.upper(),
                        'position': position
                    })
    
    def load_from_api_new(self, home_lineup_url: str, home_players_url: str,
                          away_lineup_url: str, away_players_url: str) -> LineupData:
        """
        Load lineup from NEW Hockeyettan API (2026 format).
        Uses ClubId-based endpoints with vMix field names.
        """
        lineup = LineupData()
        lineup.metadata["source"] = "api_new"
        lineup.metadata["created"] = datetime.now().isoformat()
        
        try:
            # Fetch home team players
            print(f"Fetching home players from: {home_players_url}")
            with urlopen(home_players_url, timeout=10) as response:
                home_data = json.loads(response.read().decode('utf-8'))
            
            # Fetch away team players
            print(f"Fetching away players from: {away_players_url}")
            with urlopen(away_players_url, timeout=10) as response:
                away_data = json.loads(response.read().decode('utf-8'))
            
            # Parse home team
            if 'value' in home_data and isinstance(home_data['value'], list):
                self._parse_players_api(lineup.home_team, home_data['value'])
            
            # Parse away team
            if 'value' in away_data and isinstance(away_data['value'], list):
                self._parse_players_api(lineup.away_team, away_data['value'])
            
            print(f"API import: {len(lineup.home_team.players)} home, {len(lineup.away_team.players)} away")
            
            return lineup
            
        except Exception as e:
            raise RuntimeError(f"API fetch failed: {e}")
    
    def _parse_players_api(self, team: dict, players_array: list):
        """
        Parse players from NEW API format.
        Format: [{ShirtNR.Text, Namn.Text, PositionData.Text, Titel.Text, Logo.Source, ...}]
        """
        for item in players_array:
            # Check if this is a player (has number) or staff (has "Coach" in ShirtNR)
            shirt_nr = item.get('ShirtNR.Text', '')
            
            if isinstance(shirt_nr, str) and 'coach' in shirt_nr.lower():
                # This is staff
                role_map = {
                    'head coach': 'Huvudtränare',
                    'assistant coach': 'Assisterande tränare'
                }
                role = role_map.get(shirt_nr.lower(), shirt_nr)
                
                name = item.get('Namn.Text', '').strip()
                if name:
                    team['staff'].append({'role': role, 'name': name})
            
            else:
                # This is a player
                number = str(shirt_nr) if shirt_nr else ''
                name = item.get('Namn.Text', '') or item.get('PlayerName.Text', '')
                position_raw = item.get('PositionData.Text', 'F')
                
                # Convert position codes to F/D/G
                position = 'F'  # Default
                if position_raw:
                    pos_upper = position_raw.upper()
                    if 'G' in pos_upper or 'GOAL' in pos_upper:
                        position = 'G'
                    elif 'D' in pos_upper or 'DEF' in pos_upper or 'BACK' in pos_upper:
                        position = 'D'
                    else:
                        position = 'F'
                
                if number and name:
                    team['players'].append({
                        'number': number,
                        'name': name.upper(),
                        'position': position
                    })
            
            # Extract team name and logo if present
            if 'Titel.Text' in item and not team['name']:
                team['name'] = item['Titel.Text']
            
            if 'Logo.Source' in item and not team['logo']:
                team['logo'] = item['Logo.Source']
    
    def load_from_api(self, lineup_url: str, players_url: str) -> LineupData:
        """
        Load lineup data from API endpoints.
        Handles multiple response formats automatically.
        """
        lineup = LineupData()
        lineup.metadata["source"] = "api"
        lineup.metadata["created"] = datetime.now().isoformat()
        lineup.metadata["lineup_url"] = lineup_url
        lineup.metadata["players_url"] = players_url
        
        try:
            # Fetch lineup data
            print(f"Fetching lineup from: {lineup_url}")
            with urlopen(lineup_url, timeout=10) as response:
                raw_data = json.loads(response.read().decode('utf-8'))
            
            print(f"Response type: {type(raw_data)}")
            
            # Handle LIST response: [{team1}, {team2}]
            if isinstance(raw_data, list):
                print(f"List format: {len(raw_data)} items")
                
                if len(raw_data) == 0:
                    raise RuntimeError("API returnerade tom lista - kontrollera Match ID")
                
                if len(raw_data) == 1:
                    # Special case: Single object with vMix field names
                    # Format: [{"H_GK1_name.Text": "...", "H_GK1_number.Text": 1, "A_GK1_name.Text": "...", ...}]
                    item = raw_data[0]
                    
                    # Verify it's a dict, not a string
                    if not isinstance(item, dict):
                        raise RuntimeError(f"API returnerade oväntat format: {type(item).__name__}")
                    
                    print("vMix field format detected")
                    self._parse_vmix_fields(lineup, item)
                    
                elif len(raw_data) >= 2:
                    self._parse_team_from_object(lineup.home_team, raw_data[0])
                    self._parse_team_from_object(lineup.away_team, raw_data[1])
                else:
                    raise RuntimeError(f"Expected 1-2 items, got {len(raw_data)}")
            
            # Handle DICT response
            elif isinstance(raw_data, dict):
                keys = list(raw_data.keys())
                print(f"Dict format. Keys: {keys[:5]}")
                
                if "home" in raw_data:
                    self._parse_team_from_object(lineup.home_team, raw_data["home"])
                if "away" in raw_data:
                    self._parse_team_from_object(lineup.away_team, raw_data["away"])
                    
                if "homeTeam" in raw_data:
                    lineup.home_team["name"] = raw_data["homeTeam"].get("name", "")
                if "awayTeam" in raw_data:
                    lineup.away_team["name"] = raw_data["awayTeam"].get("name", "")
                
                for player in raw_data.get("homePlayers", []):
                    lineup.home_team["players"].append({
                        "number": str(player.get("number", player.get("jerseyNumber", ""))),
                        "name": player.get("name", player.get("fullName", "")),
                        "position": player.get("position", "")
                    })
                
                for player in raw_data.get("awayPlayers", []):
                    lineup.away_team["players"].append({
                        "number": str(player.get("number", player.get("jerseyNumber", ""))),
                        "name": player.get("name", player.get("fullName", "")),
                        "position": player.get("position", "")
                    })
            
            print(f"✓ Parsed {len(lineup.home_team['players'])} home, {len(lineup.away_team['players'])} away")
            
            self.lineup_data = lineup
            return lineup
            
        except URLError as e:
            raise RuntimeError(f"Network error: {e}")
        except json.JSONDecodeError as e:
            raise RuntimeError(f"Invalid JSON: {e}")
        except Exception as e:
            import traceback
            traceback.print_exc()
            raise RuntimeError(f"API error: {e}")
    def _parse_team_data(self, team_dict: dict, data: dict):
        """Parse team data from API response"""
        team_dict["name"] = data.get("name", "")
        team_dict["logo"] = data.get("logo", "")
        
        # Parse players
        if "players" in data:
            for player in data["players"]:
                team_dict["players"].append({
                    "number": str(player.get("number", player.get("jerseyNumber", ""))),
                    "name": player.get("name", player.get("fullName", "")),
                    "position": player.get("position", "")
                })
        
        # Parse staff
        if "staff" in data:
            for staff_member in data["staff"]:
                team_dict["staff"].append({
                    "role": staff_member.get("role", ""),
                    "name": staff_member.get("name", "")
                })

    
    def _enrich_with_player_details(self, lineup: LineupData, players_data: dict):
        """Enrich lineup with additional player details from players endpoint"""
        # If players_data has additional info, merge it
        # This depends on the API structure
        pass
    
    # ========================================
    # Load/Save from file
    # ========================================
    
    def save_to_file(self, filepath: str = None) -> str:
        """
        Save current lineup data to JSON file.
        Returns filepath.
        """
        if not self.lineup_data:
            raise ValueError("No lineup data to save")
        
        if filepath is None:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filepath = os.path.join(self.cache_dir, f"lineup_{timestamp}.json")
        
        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(self.lineup_data.to_dict(), f, indent=2, ensure_ascii=False)
        
        return filepath
    
    def load_from_file(self, filepath: str) -> LineupData:
        """Load lineup data from JSON file"""
        with open(filepath, 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        self.lineup_data = LineupData.from_dict(data)
        return self.lineup_data
    
    def list_saved_lineups(self) -> List[Tuple[str, dict]]:
        """
        List all saved lineup files.
        Returns list of (filepath, metadata) tuples.
        """
        lineups = []
        
        if not os.path.exists(self.cache_dir):
            return lineups
        
        for filename in os.listdir(self.cache_dir):
            if filename.endswith('.json'):
                filepath = os.path.join(self.cache_dir, filename)
                try:
                    with open(filepath, 'r', encoding='utf-8') as f:
                        data = json.load(f)
                        metadata = data.get("metadata", {})
                        metadata["filepath"] = filepath
                        metadata["filename"] = filename
                        lineups.append((filepath, metadata))
                except Exception:
                    continue
        
        # Sort by creation date (newest first)
        lineups.sort(key=lambda x: x[1].get("created", ""), reverse=True)
        return lineups
    
    # ========================================
    # Data access methods
    # ========================================
    
    def get_players(self, side: str) -> List[dict]:
        """
        Get player list for a team.
        
        Args:
            side: "home" or "away"
        
        Returns:
            List of {"number": "1", "name": "...", "position": ""}
        """
        if not self.lineup_data:
            return []
        
        if side == "home":
            return self.lineup_data.home_team.get("players", [])
        elif side == "away":
            return self.lineup_data.away_team.get("players", [])
        else:
            return []
    
    def get_staff(self, side: str) -> List[dict]:
        """
        Get staff list for a team.
        
        Args:
            side: "home" or "away"
        
        Returns:
            List of {"role": "...", "name": ""}
        """
        if not self.lineup_data:
            return []
        
        if side == "home":
            return self.lineup_data.home_team.get("staff", [])
        elif side == "away":
            return self.lineup_data.away_team.get("staff", [])
        else:
            return []
    
    def get_team_name(self, side: str) -> str:
        """Get team name"""
        if not self.lineup_data:
            return ""
        
        if side == "home":
            return self.lineup_data.home_team.get("name", "")
        elif side == "away":
            return self.lineup_data.away_team.get("name", "")
        else:
            return ""
    
    def add_staff_member(self, side: str, role: str, name: str):
        """Add staff member to team"""
        if not self.lineup_data:
            self.lineup_data = LineupData()
        
        staff_member = {"role": role, "name": name}
        
        if side == "home":
            self.lineup_data.home_team["staff"].append(staff_member)
        elif side == "away":
            self.lineup_data.away_team["staff"].append(staff_member)
    
    def set_team_info(self, side: str, name: str = None, logo: str = None):
        """Set team name and/or logo"""
        if not self.lineup_data:
            self.lineup_data = LineupData()
        
        if side == "home":
            if name is not None:
                self.lineup_data.home_team["name"] = name
            if logo is not None:
                self.lineup_data.home_team["logo"] = logo
        elif side == "away":
            if name is not None:
                self.lineup_data.away_team["name"] = name
            if logo is not None:
                self.lineup_data.away_team["logo"] = logo
    
    def _parse_team_from_object(self, team_dict: dict, team_obj: dict):
        """Parse team data from a team object - handles multiple field name variations"""
        if not isinstance(team_obj, dict):
            return
        
        # Team name - try multiple possible keys
        team_dict["name"] = (
            team_obj.get("name") or 
            team_obj.get("teamName") or 
            team_obj.get("team") or 
            ""
        )
        
        # Logo
        team_dict["logo"] = team_obj.get("logo", "")
        
        # Players - try multiple possible keys
        players_list = (
            team_obj.get("players") or 
            team_obj.get("lineup") or 
            team_obj.get("roster") or 
            []
        )
        
        for player in players_list:
            if isinstance(player, dict):
                team_dict["players"].append({
                    "number": str(player.get("number", player.get("jerseyNumber", player.get("jersey", "")))),
                    "name": player.get("name", player.get("fullName", player.get("playerName", ""))),
                    "position": player.get("position", player.get("pos", ""))
                })
        
        # Staff
        for staff in team_obj.get("staff", []):
            if isinstance(staff, dict):
                team_dict["staff"].append({
                    "role": staff.get("role", staff.get("title", "")),
                    "name": staff.get("name", "")
                })

    def _parse_vmix_fields(self, lineup: LineupData, fields: dict):
        """
        Parse vMix field format from API.
        Format: {"H_GK1_name.Text": "NAME", "H_GK1_number.Text": 1, "A_GK1_name.Text": "NAME", ...}
        
        H_ = Home team, A_ = Away team
        Positions: GK (goalie), LD/RD (defense), LW/C/RW (forwards), XD (extra defense)
        """
        # Get team names
        lineup.home_team["name"] = fields.get("H_TeamName.Text", "")
        lineup.away_team["name"] = fields.get("A_TeamName.Text", "")
        
        # Get team logos
        lineup.home_team["logo"] = fields.get("H_TeamLogo.Source", "")
        lineup.away_team["logo"] = fields.get("A_TeamLogo.Source", "")
        
        # Parse players - check all possible position prefixes
        positions = ["GK", "LD", "RD", "LW", "C", "RW", "XD"]
        
        # Home team
        for pos in positions:
            for i in range(1, 6):  # 1-5 slots per position
                name_key = f"H_{pos}{i}_name.Text"
                number_key = f"H_{pos}{i}_number.Text"
                
                name = fields.get(name_key, "").strip()
                number = str(fields.get(number_key, "")).strip()
                
                if name and number:  # Only add if both name and number exist
                    lineup.home_team["players"].append({
                        "number": number,
                        "name": name,
                        "position": pos
                    })
        
        # Away team
        for pos in positions:
            for i in range(1, 6):
                name_key = f"A_{pos}{i}_name.Text"
                number_key = f"A_{pos}{i}_number.Text"
                
                name = fields.get(name_key, "").strip()
                number = str(fields.get(number_key, "")).strip()
                
                if name and number:
                    lineup.away_team["players"].append({
                        "number": number,
                        "name": name,
                        "position": pos
                    })
        
        print(f"Parsed from vMix fields: {len(lineup.home_team['players'])} home, {len(lineup.away_team['players'])} away")
