# SLH SETUP STUDIO v5.0

**Förbered allt INNAN sändning**

Modern desktop-app för att konfigurera säsonger, importera lag, förbered matcher och exportera data till vMix.

---

## 📋 ÖVERSIKT

SLH Setup Studio separerar **förberedelse** från **live-produktion**.

### WORKFLOW:

```
1. SÄSONG   → Skapa säsong (ISHOCKEY 25/26)
2. LAG      → Importera alla lag (API/SweHockey)
3. MATCH    → Välj match (Match ID eller Club ID)
4. LINEUP   → Editera spelarlista
5. EXPORT   → Skapa JSON-filer för vMix
6. STARTA   → Kör SLH Live (v4.x)
```

---

## 🚀 STARTA APPEN

```bash
cd slh_setup
python main.py
```

**Fönster:** 1080x720 (resizable)  
**Design:** Modern, clean, desktop-fokuserad

---

## 📂 FIL-STRUKTUR

```
slh_setup/
├── main.py                    # Huvudapp
├── config/
│   └── seasons.json          # Alla säsonger
├── data/
│   ├── teams/                # Lag per serie
│   │   ├── ISHOCKEY_25_26_NORRA.json
│   │   └── ISHOCKEY_25_26_SÖDRA.json
│   ├── matches/              # Match-data
│   │   └── 1010540.json
│   └── exports/              # JSON för vMix
│       ├── lineup.json
│       ├── scoreboard.json
│       └── match.json
├── gui/
│   ├── main_window.py        # Huvudfönster
│   └── season_manager.py     # Flik 1: Säsonger
└── core/
    ├── data_models.py        # Dataklasser
    └── data_manager.py       # Spara/ladda data
```

---

## 🎯 STEG 1: SÄSONG

### **Skapa ny säsong:**

1. Sport: `ISHOCKEY` (eller lägg till egen)
2. Säsong: `25/26`
3. Serier:
   - Lägg till `NORRA` (20 lag)
   - Lägg till `SÖDRA` (20 lag)
4. **SKAPA SÄSONG**

### **Resultat:**

```json
{
  "ISHOCKEY": {
    "25/26": {
      "sport": "ISHOCKEY",
      "year": "25/26",
      "series": {
        "NORRA": {
          "name": "NORRA",
          "num_teams": 20,
          "teams": []
        },
        "SÖDRA": {
          "name": "SÖDRA",
          "num_teams": 20,
          "teams": []
        }
      }
    }
  }
}
```

Sparas i: `config/seasons.json`

---

## 🎯 STEG 2: LAG (Coming in v5.1)

Importera lag från:
- **API:** `https://vmix-new.hockeyettan.se/api/tabel/18270`
- **SweHockey:** Web scraping
- **Manuellt:** Lägg till själv

### **Auto-extrahering från API:**

```json
{
  "Team01t.Text": "Hudiksvalls HC",
  "Team01.Source": "https://vmix-new.hockeyettan.se/scoreImages/HUD.png"
}
```

**Extraherar automatiskt:**
- ✅ Fullständigt namn: `Hudiksvalls HC`
- ✅ Logo URL: `https://.../HUD.png`
- ✅ Short name: `HUD`

**Lägg till manuellt:**
- Club ID: `442`

---

## 🎯 STEG 3: MATCH (Coming in v5.2)

### **Starta match:**

1. Välj säsong: `ISHOCKEY 25/26`
2. Välj serie: `NORRA`
3. Match:
   - **Match ID:** `1010540`
   - **Club ID:** `442` (Hudiksvalls HC)
   - **Manuellt:** Välj hemma/borta

### **Auto-fetch:**

Hämtar automatiskt från:
- SweHockey (spelare + ledare)
- API (bilder, kategorier)
- Säsongsdata (logos, shortnames)

---

## 🎯 STEG 4: LINEUP (Coming in v5.3)

Editera lineup:
- ✅ Lägg till spelare
- ✅ Lägg till ledare
- ✅ Ändra kategorier (GK1, LD2, RW3...)
- ✅ Ladda spelarbilder
- ✅ Validera före export

---

## 🎯 STEG 5: EXPORT (Coming in v5.4)

Exportera till vMix:
- `lineup.json` - All lineup-data
- `scoreboard.json` - Lag + logos
- `match.json` - Match-info
- `teams.json` - Säsongsdata

**Skriv även direkt till vMix XML:**
- SCOREBOARD UPPE
- SCOREBOARD NERE
- LINEUP HEMMA
- LINEUP BORTA

---

## 💡 DESIGN-PRINCIPER

### **Modern & Clean:**
- Stor text (11-20pt)
- Tydliga färger
- Mycket whitespace
- Professionell look

### **Desktop-first:**
- 1080x720 default
- Resizable
- Inga mobil-kompromisser

### **Step-by-step:**
- Tydligt flöde
- Validering per steg
- Kan inte gå vidare om data saknas

---

## 🔧 TEKNISK STACK

**Framework:** tkinter (standard Python)  
**Python:** 3.8+  
**Dependencies:** Inga (för steg 1)

**Senare:**
- `requests` (API calls)
- `beautifulsoup4` (SweHockey scraping)
- `Pillow` (Bildhantering)

---

## 🎨 FÄRGSCHEMA

```python
Sidebar:       #2c3e50  (Mörk grå-blå)
Accent:        #3498db  (Ljusblå)
Success:       #27ae60  (Grön)
Danger:        #e74c3c  (Röd)
Background:    #f5f5f5  (Ljusgrå)
Text:          #2c3e50  (Mörk)
Subtle:        #7f8c8d  (Grå)
```

---

## 🚀 ROADMAP

### **v5.0** ✅ (NU)
- [x] Huvudfönster
- [x] Steg-navigation
- [x] Säsongs-manager
- [x] Skapa säsonger
- [x] Spara/ladda data

### **v5.1** (Nästa)
- [ ] Lag-import från API
- [ ] Lag-import från SweHockey
- [ ] Logo auto-extrahering
- [ ] Club ID mapping

### **v5.2**
- [ ] Match-setup
- [ ] Auto-fetch lineup
- [ ] Team selection

### **v5.3**
- [ ] Lineup editor
- [ ] Add player/staff dialogs
- [ ] Image upload
- [ ] Validation

### **v5.4**
- [ ] Export manager
- [ ] JSON creation
- [ ] vMix XML write
- [ ] Integration test

### **v5.5**
- [ ] Launch SLH Live från Setup
- [ ] Pass data till v4.x
- [ ] Komplett workflow

---

## 📖 ANVÄNDNING

### **Första gången:**

1. Starta Setup Studio
2. Skapa säsong (ISHOCKEY 25/26)
3. Lägg till serier (NORRA, SÖDRA)
4. Importera lag (API/SweHockey)
5. Gå till "nästa match"

### **Varje match:**

1. Starta Setup Studio
2. Välj säsong
3. Ange Match ID
4. Granska lineup
5. Exportera
6. Starta SLH Live

---

## 🎯 FÖRDELAR

✅ **Oberoende** - Bygger data ÅT vMix  
✅ **Komplett** - All data INNAN match  
✅ **Flexibelt** - Flera källor (API, SweHockey, manuellt)  
✅ **Pålitligt** - Validering före export  
✅ **Offline** - Cache-support inbyggt  

---

## 🔗 INTEGRATION MED v4.x

Setup Studio **FÖRBEREDER**, v4.x **PRODUCERAR**:

```
Setup Studio → Exporterar filer → v4.x läser → Live-produktion
```

**Inget beroende på vMix XML!**  
Setup Studio bygger filerna, vMix läser dem.

---

## 📞 SUPPORT

Issues: GitHub  
Dokumentation: README.md + kod-kommentarer

---

**SLH Setup Studio v5.0 - Förbered professionellt! 🚀**
