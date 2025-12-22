# MLS Injury Data Collection

Automated collection of MLS player injury data with performance metrics for injury recovery analysis.

## Overview

This project collects comprehensive injury data for Major League Soccer (MLS) players including:
- Player demographics (name, position, team)
- Injury details (type, grade, date, duration)
- Performance metrics before and after injury
- Historical data spanning 2015-2024 (longest available span)

## Data Sources

### Primary Source: Transfermarkt
- **URL**: https://www.transfermarkt.us
- **Coverage**: 2015-2024 (9-10 seasons)
- **Data Points**:
  - Player injury history
  - Injury type and severity
  - Days out / Games missed
  - Performance statistics by season

### Data Validation Source
- Medical recovery timelines from peer-reviewed research (see `injury_recovery_timelines.csv`)
- Citations from MLS Injury Surveillance Database studies (2010-2021)

## Data Fields Collected

### Injury Data (`mls_player_injuries.csv`)
| Field | Description | Source |
|-------|-------------|--------|
| `player_id` | Unique player identifier | Generated |
| `player_name` | Full player name | Transfermarkt |
| `position` | Player position | Transfermarkt |
| `team` | MLS team | Transfermarkt |
| `season` | Season year | Transfermarkt |
| `injury_date` | Date injury occurred | Transfermarkt |
| `injury_type` | Type of injury (e.g., "Hamstring Strain") | Transfermarkt |
| `injury_grade` | Severity grade (if available) | Transfermarkt |
| `return_date` | Date returned to play | Transfermarkt |
| `days_out` | Number of days out | Transfermarkt |
| `games_missed` | Number of games missed | Transfermarkt |

### Performance Data (Enhanced)
| Field | Description |
|-------|-------------|
| `games_before` | Games played before injury (season) |
| `minutes_before` | Minutes played before injury |
| `goals_before` | Goals scored before injury |
| `assists_before` | Assists before injury |
| `games_after` | Games played after return |
| `minutes_after` | Minutes played after return |
| `goals_after` | Goals after return |
| `assists_after` | Assists after return |
| `performance_before_injury` | Goals+Assists per 90 min before |
| `performance_after_injury` | Goals+Assists per 90 min after |

## Installation

### Prerequisites
- Python 3.8 or higher
- pip package manager

### Setup
```bash
# Install required packages
pip install -r requirements.txt
```

## Usage

### 1. Collect Injury Data

```bash
python scrape_mls_injuries.py
```

This will:
- Scrape injury data for all MLS teams from 2015-2024
- Save results to `mls_player_injuries.csv`
- Include rate limiting (3 second delay between requests)
- Log progress and summary statistics

**Estimated Runtime**: 2-4 hours (depends on number of players/teams)

### 2. Enhance with Performance Data

```bash
python collect_performance_data.py
```

This will:
- Read `mls_player_injuries.csv`
- Collect performance statistics for each player
- Calculate metrics before/after injury
- Save enhanced data to `mls_player_injuries_enhanced.csv`

**Estimated Runtime**: 1-2 hours

### 3. Custom Seasons

```python
from scrape_mls_injuries import TransfermarktScraper

scraper = TransfermarktScraper(delay=3.0)

# Collect specific seasons
df = scraper.scrape_mls_injuries(
    seasons=["2022", "2023", "2024"],
    output_file="recent_injuries.csv"
)
```

## Data Quality Considerations

### Strengths
- **Long historical span**: 2015-2024 (9-10 seasons)
- **Comprehensive coverage**: All MLS teams and players
- **Validated against research**: Medical timelines from peer-reviewed studies
- **Standardized format**: Consistent data structure

### Limitations
- **Injury grade**: Not always specified in Transfermarkt data
- **Performance granularity**: Season-level stats (not game-by-game)
- **Data lag**: Transfermarkt updates may lag real-time injuries
- **Missing data**: Some older records may be incomplete

### Best Practices
1. **Rate limiting**: Use 2-3 second delays to respect server resources
2. **Validation**: Cross-reference with medical recovery timelines
3. **Data cleaning**: Check for duplicate records and missing values
4. **Updates**: Re-run collection periodically for current season data

## Expected Data Volume

Based on typical MLS injury patterns (from research):
- **Annual injuries**: ~1,500-2,000 per season
- **10 seasons (2015-2024)**: ~15,000-20,000 total injury records
- **Unique players**: ~1,500-2,000 players
- **Most common injuries**:
  - Hamstring strains (12.3%)
  - Ankle sprains (8.5%)
  - Adductor strains (7.6%)
  - ACL tears (varies)

## Validation Against Research

The collected data can be validated against peer-reviewed benchmarks in `injury_recovery_timelines.csv`:

Example validation queries:
```python
import pandas as pd

# Load data
injuries = pd.read_csv('mls_player_injuries_enhanced.csv')
benchmarks = pd.read_csv('injury_recovery_timelines.csv')

# Compare hamstring strain recovery times
hamstring_data = injuries[injuries['injury_type'].str.contains('Hamstring', case=False)]
avg_recovery = hamstring_data['days_out'].mean()

# Compare to benchmark (19.7 days for 2016-2021)
benchmark = benchmarks[benchmarks['injury_type'] == 'Hamstring Strain']['median_recovery_days'].mean()

print(f"Collected data average: {avg_recovery:.1f} days")
print(f"Research benchmark: {benchmark:.1f} days")
```

## Ethical & Legal Considerations

### Web Scraping Ethics
- **Rate limiting**: 3 second delays between requests
- **Respect robots.txt**: Check Transfermarkt's robots.txt
- **Terms of Service**: Review Transfermarkt TOS before large-scale scraping
- **Attribution**: Data source attribution required

### Data Privacy
- All data is publicly available on Transfermarkt
- No private medical information collected
- Player names and statistics are public domain

### Academic Use
- Suitable for research and analysis
- Cite data sources appropriately
- Consider requesting MLS Injury Surveillance Database access for academic research

## Troubleshooting

### Common Issues

**1. Connection errors / timeouts**
```python
# Increase delay between requests
scraper = TransfermarktScraper(delay=5.0)
```

**2. HTML structure changes**
- Transfermarkt may update their HTML structure
- Check scraper logs for parsing errors
- Update CSS selectors in scraper code

**3. Empty results**
- Verify Transfermarkt URLs are still valid
- Check network connectivity
- Review Transfermarkt's robots.txt for access changes

**4. Missing performance data**
- Some players may not have complete statistics
- Performance data may not be available for all seasons
- Check individual player pages on Transfermarkt

## Future Enhancements

Potential improvements to data collection:

1. **Game-by-game performance data**
   - Scrape detailed match statistics
   - Calculate pre/post injury performance with finer granularity

2. **Additional data sources**
   - FBref for advanced metrics (xG, xA, etc.)
   - MLS official statistics
   - Injury severity grades from medical sources

3. **Real-time monitoring**
   - Automated daily/weekly updates
   - Alert system for new injuries

4. **Expanded metrics**
   - Physical fitness data (if available)
   - Training load metrics
   - Positional heat maps

5. **Database migration**
   - Move from CSV to SQLite/PostgreSQL
   - Enable complex queries and relationships

## References

### Data Sources
- [Transfermarkt MLS](https://www.transfermarkt.us/major-league-soccer/startseite/wettbewerb/MLS1)
- [worldfootballR R Package](https://github.com/JaseZiv/worldfootballR) - Inspiration for injury data collection

### Research Citations
See `citations.csv` for peer-reviewed studies on MLS injury data:
- MLS Injury Surveillance Database (2010-2021)
- Hamstring injury studies (2014-2024)
- ACL reconstruction outcomes
- General soccer injury epidemiology

## Support

For issues or questions:
1. Check the troubleshooting section
2. Review Transfermarkt's website structure
3. Verify network connectivity and rate limits
4. Check logs for specific error messages

## License

Data collection scripts: [Specify your license]
Collected data: Subject to Transfermarkt terms of use
Medical reference data: Cited from peer-reviewed research (see citations.csv)
