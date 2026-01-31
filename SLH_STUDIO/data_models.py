"""
Data models for SLH Setup Studio
Clean, typed data structures
"""

from dataclasses import dataclass, field
from typing import List, Dict, Optional
from datetime import datetime


@dataclass
class Team:
    """Represents a team in a series"""
    name: str
    short_name: str
    club_id: Optional[str] = None
    logo_small: Optional[str] = None  # URL or path
    logo_large: Optional[str] = None  # URL or path
    position: Optional[int] = None
    
    def to_dict(self) -> dict:
        return {
            'name': self.name,
            'short_name': self.short_name,
            'club_id': self.club_id,
            'logo_small': self.logo_small,
            'logo_large': self.logo_large,
            'position': self.position
        }
    
    @classmethod
    def from_dict(cls, data: dict) -> 'Team':
        return cls(**data)


@dataclass
class Series:
    """Represents a series (NORRA, SÖDRA, etc.)"""
    name: str
    num_teams: int
    api_id: Optional[str] = None
    teams: List[Team] = field(default_factory=list)
    
    def to_dict(self) -> dict:
        return {
            'name': self.name,
            'num_teams': self.num_teams,
            'api_id': self.api_id,
            'teams': [t.to_dict() for t in self.teams]
        }
    
    @classmethod
    def from_dict(cls, data: dict) -> 'Series':
        teams = [Team.from_dict(t) for t in data.get('teams', [])]
        return cls(
            name=data['name'],
            num_teams=data['num_teams'],
            api_id=data.get('api_id'),
            teams=teams
        )


@dataclass
class Season:
    """Represents a season"""
    sport: str
    year: str  # e.g. "25/26"
    series: Dict[str, Series] = field(default_factory=dict)
    created: str = field(default_factory=lambda: datetime.now().isoformat())
    
    def to_dict(self) -> dict:
        return {
            'sport': self.sport,
            'year': self.year,
            'series': {name: s.to_dict() for name, s in self.series.items()},
            'created': self.created
        }
    
    @classmethod
    def from_dict(cls, data: dict) -> 'Season':
        series = {
            name: Series.from_dict(s) 
            for name, s in data.get('series', {}).items()
        }
        return cls(
            sport=data['sport'],
            year=data['year'],
            series=series,
            created=data.get('created', datetime.now().isoformat())
        )


@dataclass
class Player:
    """Represents a player"""
    number: str
    name: str
    position: str  # GK, D, F
    category: Optional[str] = None  # GK1, LD2, RW3, etc.
    image_url: Optional[str] = None
    
    def to_dict(self) -> dict:
        return {
            'number': self.number,
            'name': self.name,
            'position': self.position,
            'category': self.category,
            'image_url': self.image_url
        }
    
    @classmethod
    def from_dict(cls, data: dict) -> 'Player':
        return cls(**data)


@dataclass
class Staff:
    """Represents a staff member (coach, etc.)"""
    name: str
    role: str  # Huvudtränare, Assisterande tränare, etc.
    
    def to_dict(self) -> dict:
        return {
            'name': self.name,
            'role': self.role
        }
    
    @classmethod
    def from_dict(cls, data: dict) -> 'Staff':
        return cls(**data)


@dataclass
class TeamLineup:
    """Represents a team's lineup for a match"""
    team: Team
    players: List[Player] = field(default_factory=list)
    staff: List[Staff] = field(default_factory=list)
    
    def to_dict(self) -> dict:
        return {
            'team': self.team.to_dict(),
            'players': [p.to_dict() for p in self.players],
            'staff': [s.to_dict() for s in self.staff]
        }
    
    @classmethod
    def from_dict(cls, data: dict) -> 'TeamLineup':
        return cls(
            team=Team.from_dict(data['team']),
            players=[Player.from_dict(p) for p in data.get('players', [])],
            staff=[Staff.from_dict(s) for s in data.get('staff', [])]
        )


@dataclass
class Match:
    """Represents a match"""
    match_id: Optional[str] = None
    home: Optional[TeamLineup] = None
    away: Optional[TeamLineup] = None
    date: Optional[str] = None
    venue: Optional[str] = None
    series: Optional[str] = None
    
    def to_dict(self) -> dict:
        return {
            'match_id': self.match_id,
            'home': self.home.to_dict() if self.home else None,
            'away': self.away.to_dict() if self.away else None,
            'date': self.date,
            'venue': self.venue,
            'series': self.series
        }
    
    @classmethod
    def from_dict(cls, data: dict) -> 'Match':
        return cls(
            match_id=data.get('match_id'),
            home=TeamLineup.from_dict(data['home']) if data.get('home') else None,
            away=TeamLineup.from_dict(data['away']) if data.get('away') else None,
            date=data.get('date'),
            venue=data.get('venue'),
            series=data.get('series')
        )
