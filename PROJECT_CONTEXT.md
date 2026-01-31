# SLH Setup Studio v5.1.2 - Projektkontext

## Bakgrund

Vi bygger SLH Setup Studio - en ny desktop-app (1080x720) för att förbereda data INNAN broadcast. Detta är en omstart från scratch, separerad från den gamla mobila live-appen (v4.x).

### Filosofi-ändring

```
GAMMALT (v4.x): vMix XML → SLH läser → Hoppas data finns ❌
NYTT (v5.x):    SLH Setup → Bygger data → Exporterar → vMix läser ✅
```

## Nuvarande Status: v5.1.2

### ✅ Färdigt

**STEG 1: SÄSONG**
- Skapa säsonger (Sport, År, Serier)
- Spara/ladda från config/seasons.json
- Modern GUI med två kolumner

**STEG 2: LAG**
- Importera från API JSON-filer (TabellNorra.txt / TabellSödra.txt)
- Auto-extraherar: FullName, ShortName, Logo URLs
- Editerbar tabell med Club ID-fält
- Spara till data/teams/ISHOCKEY_25_26_NORRA.json

### 🚧 Återstår

**STEG 3: MATCH (v5.2)**
- Välj match från dagens matcher
- Hämta lineup från API/SweHockey
- Auto-populate med sparad lag-info

**STEG 4: LINEUP (v5.3)**
- Editera spelarlista
- Lägg till spelare/ledare
- Kategorisering (GK1, LD2, RW3...)

**STEG 5: EXPORT (v5.4)**
- Skapa JSON-filer för vMix
- Skriv direkt till vMix XML

## Teknisk Stack

```
slh_setup/
├── main.py                    # Entry point
├── config/
│   └── seasons.json          # Sparade säsonger
├── data/
│   ├── teams/                # Lag per serie
│   ├── matches/              # Match-data
│   └── exports/              # JSON för vMix
├── gui/
│   ├── main_window.py        # Huvudfönster med 5-stegs nav
│   ├── season_manager.py     # Steg 1
│   └── team_importer.py      # Steg 2
└── core/
    ├── data_models.py        # Season, Team, Player etc
    ├── data_manager.py       # JSON persistence
    └── api_parser.py         # Parse Hockeyettan API
```

## Viktiga Endpoints

```
NORRA (18270):
- Tabell: /api/tabel/18270
- Dagens matcher: /api/round/18270

SÖDRA (18271):
- Tabell: /api/tabel/18271
- Dagens matcher: /api/round/18271

MATCH:
- Lineup: /api/lineup/{match_id}
- Pregame: /api/pregame/{match_id}
- Players: /api/players/{match_id}
```

## Design-principer

- **Modern & Clean**: Stora texter, mycket whitespace
- **Desktop-first**: 1080x720, resizable
- **Step-by-step**: Tydligt 5-stegs flöde
- **Validering**: Kan inte gå vidare utan data
- **Färger**:
  - Sidebar: `#2c3e50`
  - Accent: `#3498db`
  - Success: `#27ae60`
  - Danger: `#e74c3c`

## Nästa Steg

Väntar på v5.1.2-koden för att bygga vidare på Steg 3: Match Setup.
