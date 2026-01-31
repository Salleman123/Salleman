# Komplett ny load_from_api som hanterar ALLA format

def load_from_api_new(self, lineup_url: str, players_url: str):
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
        
        # Handle different response types
        if isinstance(raw_data, list):
            # Response is a list: [{team1}, {team2}]
            print(f"List format detected with {len(raw_data)} items")
            
            if len(raw_data) >= 2:
                home_team = raw_data[0]
                away_team = raw_data[1]
                
                # Parse home team
                self._parse_team_from_object(lineup.home_team, home_team)
                # Parse away team  
                self._parse_team_from_object(lineup.away_team, away_team)
            else:
                raise RuntimeError(f"Expected at least 2 teams, got {len(raw_data)}")
                
        elif isinstance(raw_data, dict):
            # Response is a dict - check format
            keys = list(raw_data.keys())
            print(f"Dict format detected. Keys: {keys}")
            
            if "home" in raw_data and "away" in raw_data:
                # Format: {"home": {...}, "away": {...}}
                self._parse_team_from_object(lineup.home_team, raw_data["home"])
                self._parse_team_from_object(lineup.away_team, raw_data["away"])
                
            elif "homeTeam" in raw_data or "homePlayers" in raw_data:
                # Format: {"homeTeam": {...}, "homePlayers": [...], ...}
                if "homeTeam" in raw_data:
                    lineup.home_team["name"] = raw_data["homeTeam"].get("name", "")
                if "awayTeam" in raw_data:
                    lineup.away_team["name"] = raw_data["awayTeam"].get("name", "")
                
                # Parse players
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
            else:
                # Unknown format
                print(f"Unknown format. Full response:\n{json.dumps(raw_data, indent=2)[:1000]}")
                raise RuntimeError("Unknown API response format")
        else:
            raise RuntimeError(f"Unexpected response type: {type(raw_data)}")
        
        print(f"Parsed {len(lineup.home_team['players'])} home, {len(lineup.away_team['players'])} away players")
        
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

def _parse_team_from_object(self, team_dict: dict, team_obj: dict):
    """Parse team data from a team object"""
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
