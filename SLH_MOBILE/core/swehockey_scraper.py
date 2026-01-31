"""
SweHockey Scraper
Scrapes lineup data from stats.swehockey.se
"""

import re
import requests
from typing import Dict, List, Optional
from bs4 import BeautifulSoup


class SweHockeyScraperError(Exception):
    """Raised when scraping fails"""
    pass


class SweHockeyScraper:
    """Scrapes lineup data from SweHockey"""
    
    BASE_URL = "https://stats.swehockey.se/Game/LineUps"
    
    @staticmethod
    def _clean_staff_name(name: str) -> str:
        """
        Clean staff name by removing role prefixes and special characters
        
        Examples:
            "Å Hultin, Anders" → "Å Hultin, Anders"
            "AssistantCoach:Ola" → "Ola"
            "Head Coach" → "" (empty, not a name)
        """
        if not name:
            return ""
        
        # Remove common role keywords
        role_keywords = [
            'huvudtränare', 'head coach', 'headcoach',
            'assisterande tränare', 'assistant coach', 'assistantcoach',
            'tränare', 'coach'
        ]
        
        name_lower = name.lower()
        for keyword in role_keywords:
            if keyword in name_lower:
                # If the name IS the keyword, return empty
                if name_lower.strip() == keyword:
                    return ""
                # Remove the keyword
                name = re.sub(keyword, '', name, flags=re.IGNORECASE)
        
        # Clean up encoding artifacts
        # Remove common encoding problem characters
        artifacts = ['Ã', 'Â', 'â', '€', '™', 'š', 'œ', 'ž']
        for artifact in artifacts:
            # Only remove if it appears without adjacent normal characters
            # This preserves actual names that might contain these
            if artifact in name and len(name.strip()) > len(artifact):
                # Keep for now, might be part of name
                pass
        
        # Clean up whitespace and special chars
        name = name.strip().lstrip(':').strip()
        
        # Remove multiple spaces
        name = ' '.join(name.split())
        
        return name
    
    @staticmethod
    def scrape_lineup(match_id: str) -> Dict:
        """
        Scrape lineup from SweHockey match page
        
        Args:
            match_id: Match ID (e.g. "1010654")
            
        Returns:
            Dict with structure:
            {
                'match_info': {
                    'home_team': str,
                    'away_team': str,
                    'date': str,
                    'arena': str,
                    'score': str
                },
                'home': {
                    'team_name': str,
                    'players': [{'number': str, 'name': str, 'position': str}],
                    'staff': [{'role': str, 'name': str}]
                },
                'away': {
                    'team_name': str,
                    'players': [{'number': str, 'name': str, 'position': str}],
                    'staff': [{'role': str, 'name': str}]
                }
            }
        """
        url = f"{SweHockeyScraper.BASE_URL}/{match_id}"
        
        try:
            response = requests.get(url, timeout=10)
            response.raise_for_status()
            
            # Try multiple encodings to find the best one
            encodings_to_try = ['ISO-8859-1', 'UTF-8', 'Windows-1252', 'Latin-1']
            
            best_content = None
            best_encoding = None
            
            for encoding in encodings_to_try:
                try:
                    # Set encoding and get text
                    response.encoding = encoding
                    content = response.text
                    
                    # Check if this encoding produces valid Swedish characters
                    # Look for common Swedish characters that should be present
                    if 'Ã' not in content and 'Â' not in content:
                        # No encoding artifacts - this looks good!
                        best_content = content
                        best_encoding = encoding
                        print(f"✓ Using encoding: {encoding}")
                        break
                except:
                    continue
            
            # Fallback to ISO-8859-1 if nothing worked
            if best_content is None:
                response.encoding = 'ISO-8859-1'
                best_content = response.text
                best_encoding = 'ISO-8859-1'
                print(f"⚠ Fallback to encoding: {best_encoding}")
            
        except requests.RequestException as e:
            raise SweHockeyScraperError(f"Failed to fetch page: {e}")
        
        # Parse HTML with correctly decoded text
        soup = BeautifulSoup(best_content, 'html.parser')
        
        # Extract match info
        match_info = SweHockeyScraper._extract_match_info(soup)
        
        # Extract lineups
        home_lineup = SweHockeyScraper._extract_team_lineup(soup, is_home=True)
        away_lineup = SweHockeyScraper._extract_team_lineup(soup, is_home=False)
        
        return {
            'match_info': match_info,
            'home': home_lineup,
            'away': away_lineup
        }
    
    @staticmethod
    def _extract_match_info(soup: BeautifulSoup) -> Dict:
        """Extract match information"""
        try:
            # Title: "Hanvikens SK - Karlskrona HK"
            title = soup.find('h2', text=lambda t: ' - ' in t if t else False)
            if title:
                teams = title.text.strip().split(' - ')
                home_team = teams[0].strip()
                away_team = teams[1].strip() if len(teams) > 1 else ""
            else:
                home_team = away_team = ""
            
            # Date and time
            date_elem = soup.find('h3', text=lambda t: '2026-' in t if t else False)
            date = date_elem.text.strip() if date_elem else ""
            
            # Arena
            arena_elem = soup.find('h3', style=lambda s: 'font-weight: normal' in s if s else False)
            arena = arena_elem.find('b').text.strip() if arena_elem and arena_elem.find('b') else ""
            
            # Score
            score_div = soup.find('div', text=lambda t: 'Final Score' in t if t else False)
            if score_div:
                parent = score_div.parent
                score_text = parent.find('div', style=lambda s: 'font-size: 14px' in s if s else False)
                score = score_text.text.strip() if score_text else ""
            else:
                score = ""
            
            return {
                'home_team': home_team,
                'away_team': away_team,
                'date': date,
                'arena': arena,
                'score': score
            }
        except Exception as e:
            print(f"Warning: Could not extract match info: {e}")
            return {}
    
    @staticmethod
    def _extract_team_lineup(soup: BeautifulSoup, is_home: bool) -> Dict:
        """Extract lineup for one team using simple index-based approach"""
        try:
            # Find ALL team headers
            all_headers = soup.find_all('h3', text=lambda t: ('(Red)' in t or '(White)' in t) if t else False)
            
            if len(all_headers) < 2:
                print(f"Warning: Found {len(all_headers)} team headers, expected 2")
                return {'team_name': '', 'players': [], 'staff': []}
            
            # Select the right team
            team_header = all_headers[0] if is_home else all_headers[1]
            next_header = all_headers[1] if is_home else None
            
            # Extract team name - use get_text() for proper decoding
            team_name_raw = team_header.get_text(strip=True).split('(')[0].strip()
            # Remove "Å" artifact that sometimes appears
            team_name = team_name_raw.replace('Å', '').strip()
            
            # Find ALL player divs in the document
            all_player_divs = soup.find_all('div', class_='lineUpPlayer')
            
            # Find ALL coach cells in the document
            # Be SELECTIVE - only actual coach designations
            all_coach_cells = []
            
            # Look for <td> elements that contain coach/trainer designations
            # Must have BOTH a role keyword AND a colon separator
            for td in soup.find_all('td'):
                text = td.get_text(strip=True)
                
                # Skip empty or very short
                if not text or len(text) < 5:
                    continue
                
                # Skip separators (lines with repeated characters)
                # e.g. "ååååååååå" or "========" or "--------" or "aaaaaaaa"
                text_clean = text.replace(' ', '').replace('\n', '').replace('\t', '')
                unique_chars = len(set(text_clean))
                
                # If mostly repeated characters, it's a separator
                if unique_chars <= 3:  # Very few unique chars
                    continue
                
                # Additional check: if more than 50% same character, skip
                if text_clean:
                    most_common_char = max(set(text_clean), key=text_clean.count)
                    if text_clean.count(most_common_char) / len(text_clean) > 0.5:
                        continue
                
                # Check for explicit coach patterns with colon
                has_role = any(keyword in text.lower() for keyword in ['coach:', 'tränare:', 'trainer:'])
                has_separator = ':' in text
                
                # Must have role indicator AND colon AND reasonable length
                if has_role and has_separator and len(text) < 100:
                    all_coach_cells.append(td)
            
            # Strategy: Split lists in half
            # First half = home team, Second half = away team
            mid_players = len(all_player_divs) // 2
            mid_coaches = len(all_coach_cells) // 2
            
            if is_home:
                player_divs = all_player_divs[:mid_players]
                coach_cells = all_coach_cells[:mid_coaches]
            else:
                player_divs = all_player_divs[mid_players:]
                coach_cells = all_coach_cells[mid_coaches:]
            
            # Extract players
            players = []
            for div in player_divs:
                # Use get_text() to properly decode HTML entities
                text = div.get_text(strip=True)
                # Match "30. Forslund, Tim"
                match = re.match(r'(\d+)\.\s*(.+?,\s*.+)', text)
                if match:
                    number = match.group(1)
                    name_parts = match.group(2).split(',')
                    if len(name_parts) == 2:
                        last_name = name_parts[0].strip()
                        first_name = name_parts[1].strip()
                        # Name is already properly decoded by get_text()
                        name = f"{first_name} {last_name}".upper()
                    else:
                        name = match.group(2).strip().upper()
                    
                    players.append({
                        'number': number,
                        'name': name,
                        'position': 'F'  # Default position
                    })
            
            # Extract staff
            staff = []
            for cell in coach_cells:
                # Use get_text() to properly decode
                text = cell.get_text(strip=True)
                
                # Check patterns in order (MUST use elif to avoid duplicates!)
                if 'Head Coach:' in text or ('head coach' in text.lower() and ':' in text):
                    # Head Coach pattern
                    if 'Head Coach:' in text:
                        name = text.split('Head Coach:')[1].strip()
                    elif 'head coach:' in text.lower():
                        name = text.lower().split('head coach:')[1].strip()
                    else:
                        name = text
                    
                    # Clean up name - remove role if still present
                    name = SweHockeyScraper._clean_staff_name(name)
                    if name:
                        staff.append({'role': 'Huvudtränare', 'name': name})
                        
                elif 'Assistant Coach:' in text or ('assistant coach' in text.lower() and ':' in text):
                    # Assistant Coach pattern
                    if 'Assistant Coach:' in text:
                        name = text.split('Assistant Coach:')[1].strip()
                    elif 'assistant coach:' in text.lower():
                        name = text.lower().split('assistant coach:')[1].strip()
                    else:
                        name = text
                    
                    # Clean up name
                    name = SweHockeyScraper._clean_staff_name(name)
                    if name:
                        staff.append({'role': 'Assisterande tränare', 'name': name})
                
                elif 'Huvudtränare' in text and ':' in text:
                    # Swedish: Huvudtränare
                    parts = text.split(':')
                    if len(parts) > 1:
                        name = parts[1].strip()
                    else:
                        name = text.replace('Huvudtränare', '').strip()
                    
                    name = SweHockeyScraper._clean_staff_name(name)
                    if name:
                        staff.append({'role': 'Huvudtränare', 'name': name})
                
                elif 'Assisterande' in text and 'tränare' in text.lower() and ':' in text:
                    # Swedish: Assisterande tränare
                    parts = text.split(':')
                    if len(parts) > 1:
                        name = parts[1].strip()
                    else:
                        name = text.replace('Assisterande tränare', '').strip()
                    
                    name = SweHockeyScraper._clean_staff_name(name)
                    if name:
                        staff.append({'role': 'Assisterande tränare', 'name': name})
                
                elif 'tränare' in text.lower() and ':' in text:
                    # Generic coach pattern (fallback)
                    parts = text.split(':', 1)
                    if len(parts) == 2:
                        role = parts[0].strip()
                        name = parts[1].strip()
                        if name and role:
                            staff.append({'role': role, 'name': name})
            
            print(f"Extracted {team_name}: {len(players)} players, {len(staff)} staff")
            
            # Sort players by number (numerically)
            players.sort(key=lambda p: int(p['number']) if p['number'].isdigit() else 999)
            
            return {
                'team_name': team_name,
                'players': players,
                'staff': staff
            }
            
        except Exception as e:
            print(f"Error extracting team lineup: {e}")
            import traceback
            traceback.print_exc()
            return {'team_name': '', 'players': [], 'staff': []}


def test_scraper():
    """Test the scraper with the example match"""
    scraper = SweHockeyScraper()
    
    try:
        data = scraper.scrape_lineup("1010654")
        
        print("=" * 60)
        print("MATCH INFO:")
        print(f"  Home: {data['match_info']['home_team']}")
        print(f"  Away: {data['match_info']['away_team']}")
        print(f"  Date: {data['match_info']['date']}")
        print(f"  Arena: {data['match_info']['arena']}")
        print(f"  Score: {data['match_info']['score']}")
        
        print("\nHOME TEAM:")
        print(f"  {data['home']['team_name']}")
        print(f"  Players: {len(data['home']['players'])}")
        for p in data['home']['players'][:3]:
            print(f"    {p['number']:>2} {p['name']}")
        print(f"  Staff: {len(data['home']['staff'])}")
        for s in data['home']['staff']:
            print(f"    {s['role']}: {s['name']}")
        
        print("\nAWAY TEAM:")
        print(f"  {data['away']['team_name']}")
        print(f"  Players: {len(data['away']['players'])}")
        for p in data['away']['players'][:3]:
            print(f"    {p['number']:>2} {p['name']}")
        print(f"  Staff: {len(data['away']['staff'])}")
        for s in data['away']['staff']:
            print(f"    {s['role']}: {s['name']}")
        
        print("=" * 60)
        
    except SweHockeyScraperError as e:
        print(f"Error: {e}")


if __name__ == "__main__":
    test_scraper()
