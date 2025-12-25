# MLS Player Injury Data Collection

Complete MLS player injury dataset with accurate team attributions.

## Current Dataset

**File:** `mls_player_injuries.csv`
- **28,811 injury records**
- **1,921 unique players**
- **Seasons:** 2015-2025 (through December 2024)
- **Team attribution accuracy:** 79.5% (22,910 records with correct teams)
- **Date range:** April 1, 2008 → September 9, 2024

## Quick Start

### Run Full Scraper
```bash
python3 scrape_mls_injuries.py
```
Collects injury data for MLS seasons 2015-2024 (~3-7 hours)

### Update with Latest 2025 Data
```bash
python3 scrape_2025_update.py
```
Updates with latest injuries from current season (~1-2 hours)

### Monitor Progress
```bash
bash monitor_scraper.sh           # Main scraper
bash monitor_2025_update.sh       # Update scraper
```

## Project Structure

```
Golden-bandage/
├── mls_player_injuries.csv          # MAIN DATASET (use this!)
├── scrape_mls_injuries.py           # Main scraper
├── scrape_2025_update.py            # Update script
├── collect_performance_data.py      # Performance metrics collector
├── validate_injury_data.py          # Data validation
├── monitor_scraper.sh               # Progress monitor
├── monitor_2025_update.sh           # Update monitor
├── requirements.txt                 # Python dependencies
├── citations.csv                    # Medical citations
├── README.md                        # This file
├── SCRAPER_FIX_SUMMARY.md          # Team attribution fix details
├── README_DATA_COLLECTION.md       # Detailed documentation
├── QUICKSTART.md                   # Quick reference guide
└── archive/                        # Old files and logs
    ├── data/                       # Old datasets
    ├── scripts/                    # Development scripts
    ├── logs/                       # Scraper logs
    └── docs/                       # Old documentation
```

## Data Quality

### Team Attribution Fix (December 2024)
Fixed critical bug where all injuries were attributed to players' current teams instead of the team they played for when injured.

**Example:** Ashley Cole
- **Correct:** 8 injuries → Chelsea FC (2008-2014), 2 injuries → LA Galaxy (2016-2017)
- **Before:** All 10 injuries → LA Galaxy

### Dataset Statistics
- **22,910 records (79.5%)** - Correct team attribution
- **5,901 records (20.5%)** - Missing team data (Transfermarkt limitation)
- **0 duplicates** - Checkpoint system prevents re-scraping
- **No MLS-only bias** - Includes full career injury history

## Key Features

1. **Accurate Team Attribution**
   - Extracts team from Transfermarkt injury table
   - Shows actual team at time of injury
   - Captures full career history (MLS + non-MLS)

2. **Comprehensive Data**
   - Player name, position, team
   - Injury type, date, return date
   - Days out, games missed
   - Season, Transfermarkt URL

3. **Smart Scraping**
   - Checkpoint system (resume after interruption)
   - Rate limiting (3 sec between requests)
   - Incremental updates
   - Duplicate prevention

## Column Definitions

| Column | Description |
|--------|-------------|
| `player_name` | Player's full name |
| `position` | Field position |
| `team` | Team at time of injury |
| `season` | Season (e.g., "23/24") |
| `injury_type` | Type of injury |
| `injury_date` | Date injury occurred |
| `return_date` | Date player returned |
| `days_out` | Days missed (numeric) |
| `games_missed` | Games missed (numeric) |
| `player_url` | Transfermarkt profile URL |
| `data_collection_date` | When data was scraped |

## Common Use Cases

### Load and Analyze Data
```python
import pandas as pd

# Load dataset
df = pd.read_csv('mls_player_injuries.csv')

# Filter for specific team
galaxy = df[df['team'] == 'Los Angeles Galaxy']

# Filter by injury type
hamstring = df[df['injury_type'] == 'Hamstring injury']

# Get player injury history
player = df[df['player_name'] == 'Lionel Messi']
```

### Update Dataset
```bash
# Run update scraper
python3 scrape_2025_update.py

# New data automatically merged into mls_player_injuries.csv
```

## Documentation

- **SCRAPER_FIX_SUMMARY.md** - Team attribution fix details
- **README_DATA_COLLECTION.md** - Comprehensive scraping guide
- **QUICKSTART.md** - Quick reference
- **archive/docs/** - Historical documentation

## Known Limitations

1. **20.5% missing team data** - Some Transfermarkt injury pages lack team logos
2. **Date format variations** - Transfermarkt uses different formats across regions
3. **Rate limiting** - 3-second delay required to avoid blocking
4. **Checkpoint size** - Large checkpoint files (500KB+) track processed players

## Tips

- **First time?** Run `scrape_mls_injuries.py` to build full dataset
- **Regular updates?** Run `scrape_2025_update.py` monthly
- **Interrupted?** Scraper automatically resumes from checkpoint
- **Stuck?** Check `archive/logs/scraper_output.log` for errors

## Update Schedule

**Recommended:** Run `scrape_2025_update.py` monthly during MLS season to capture latest injuries.

## Data Sources

- **Source:** Transfermarkt.us
- **Seasons:** 2015-2025
- **Teams:** All MLS teams + full career history
- **Last Updated:** December 2024

## Support

For questions about:
- **Scraper functionality:** See SCRAPER_FIX_SUMMARY.md
- **Data collection:** See README_DATA_COLLECTION.md
- **Quick reference:** See QUICKSTART.md

---

**Current Dataset:** `mls_player_injuries.csv` (4.4 MB, 28,811 records)
**Status:** Production-ready with accurate team attributions
