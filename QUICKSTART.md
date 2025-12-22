# Quick Start Guide - MLS Injury Data Collection

## Setup (5 minutes)

1. **Install dependencies:**
   ```bash
   pip install -r requirements.txt
   ```

2. **Verify installation:**
   ```bash
   python -c "import requests, bs4, pandas; print('All dependencies installed!')"
   ```

## Collecting Data

### Option 1: Full Historical Collection (Recommended)

Collect all available MLS injury data from 2015-2024:

```bash
# Step 1: Scrape injury data (2-4 hours)
python scrape_mls_injuries.py

# Step 2: Enhance with performance metrics (1-2 hours)
python collect_performance_data.py

# Step 3: Validate against medical benchmarks
python validate_injury_data.py
```

**Output files:**
- `mls_player_injuries.csv` - Raw injury data
- `mls_player_injuries_enhanced.csv` - With performance metrics
- `validation_report.txt` - Quality and benchmark comparison

### Option 2: Recent Seasons Only (Faster)

Collect only recent seasons (2022-2024):

```bash
python -c "
from scrape_mls_injuries import TransfermarktScraper
scraper = TransfermarktScraper(delay=3.0)
scraper.scrape_mls_injuries(
    seasons=['2022', '2023', '2024'],
    output_file='recent_injuries.csv'
)
"
```

### Option 3: Specific Team/Position Analysis

```python
import pandas as pd
from scrape_mls_injuries import TransfermarktScraper

scraper = TransfermarktScraper(delay=3.0)

# Collect all data
df = scraper.scrape_mls_injuries(seasons=['2023', '2024'])

# Filter for specific team
team_injuries = df[df['team'] == 'LA Galaxy']

# Filter for specific position
midfielder_injuries = df[df['position'].str.contains('Midfield', case=False)]

# Save filtered data
team_injuries.to_csv('galaxy_injuries.csv', index=False)
```

## Data Outputs

### Expected Data Volume

| Timespan | Estimated Records | File Size |
|----------|------------------|-----------|
| 2015-2024 (full) | 15,000-20,000 | 3-5 MB |
| 2022-2024 (recent) | 4,500-6,000 | 1-2 MB |
| Single season | 1,500-2,000 | 200-400 KB |

### Data Fields

**Core injury data:**
- Player info: name, position, team
- Injury: type, severity, date
- Recovery: days out, games missed
- Source: Transfermarkt URL

**Enhanced performance data:**
- Pre-injury: games, minutes, goals, assists
- Post-injury: same metrics after return
- Performance scores: goals+assists per 90 min

## Validation Against Research

Your collected data will be automatically validated against:
- MLS Injury Surveillance Database studies (2010-2021)
- Peer-reviewed recovery timelines
- Expected injury rates by type

**Key benchmarks:**
- Hamstring strains: ~19.7 days median recovery
- ACL tears: ~240 days median recovery
- Ankle sprains: ~15.8 days median recovery
- Adductor strains: ~19.7 days median recovery

## Common Use Cases

### 1. Injury Risk by Position
```python
import pandas as pd

df = pd.read_csv('mls_player_injuries_enhanced.csv')

# Group by position
risk = df.groupby('position').agg({
    'player_name': 'count',
    'days_out': 'mean'
}).rename(columns={'player_name': 'injury_count'})

print(risk.sort_values('injury_count', ascending=False))
```

### 2. Recovery Time Analysis
```python
# Compare your data to benchmarks
from validate_injury_data import InjuryDataValidator

validator = InjuryDataValidator()
comparison = validator.compare_recovery_times()
print(comparison)
```

### 3. Performance Impact
```python
# Analyze pre vs post injury performance
df = pd.read_csv('mls_player_injuries_enhanced.csv')

complete = df[df['performance_before_injury'].notna() &
              df['performance_after_injury'].notna()]

complete['perf_change'] = (
    complete['performance_after_injury'] -
    complete['performance_before_injury']
)

print(f"Average performance change: {complete['perf_change'].mean():.3f}")
print(f"Players with decline: {(complete['perf_change'] < 0).sum()}")
```

## Troubleshooting

### Issue: "No data collected"
**Solution:**
- Check internet connection
- Verify Transfermarkt is accessible: https://www.transfermarkt.us
- Increase delay: `TransfermarktScraper(delay=5.0)`

### Issue: "Rate limited / blocked"
**Solution:**
- Increase delay between requests
- Split collection into smaller batches
- Wait and retry later

### Issue: "Missing performance data"
**Solution:**
- Performance data may not be available for all players
- Check specific player pages on Transfermarkt
- Some older records may have incomplete stats

## Next Steps

After collecting data:

1. **Explore the data:**
   ```bash
   python -c "import pandas as pd; df = pd.read_csv('mls_player_injuries_enhanced.csv'); print(df.describe())"
   ```

2. **Run validation:**
   ```bash
   python validate_injury_data.py
   cat validation_report.txt
   ```

3. **Analyze patterns:**
   - Which injuries have longest recovery?
   - Which positions are most at risk?
   - How does performance change post-injury?
   - Are recovery times improving over time?

4. **Compare to medical research:**
   - See `injury_recovery_timelines.csv` for benchmarks
   - See `citations.csv` for research sources

## Data Citation

When using this data, please cite:

**Data Source:**
- Transfermarkt (https://www.transfermarkt.us)

**Medical Benchmarks:**
- See `citations.csv` for full research citations
- MLS Injury Surveillance Database (2010-2021)

## Support

For questions or issues:
1. Check [README_DATA_COLLECTION.md](README_DATA_COLLECTION.md) for detailed documentation
2. Review `validation_report.txt` for data quality metrics
3. Check script logs for error messages

## Estimated Time Investment

| Task | Time | Output |
|------|------|--------|
| Setup | 5 min | Dependencies installed |
| Full scrape (2015-2024) | 2-4 hrs | ~15,000-20,000 records |
| Performance enhancement | 1-2 hrs | Enhanced metrics |
| Validation | 1 min | Quality report |
| **Total** | **3-7 hrs** | **Complete dataset** |

For faster results, collect recent seasons only (2022-2024) in ~1-2 hours.
