# Day-of-Week Injury Analysis: Technical Methodology

## Data Source

**Field**: `injury_date` column in `mls_player_injuries_with_stadiums.csv`
**Format**: String in format `"MMM DD, YYYY"` (e.g., "May 6, 2019", "Jul 18, 2025")
**Source**: Transfermarkt.us injury database
**Total Records**: 8,497 injuries (100% successfully parsed)

## Parsing Method

```python
import pandas as pd

df = pd.read_csv('mls_player_injuries_with_stadiums.csv')

# Parse date strings to datetime objects
df['injury_date_parsed'] = pd.to_datetime(df['injury_date'], format='%b %d, %Y', errors='coerce')

# Extract day of week name (Monday, Tuesday, etc.)
df['day_of_week'] = df['injury_date_parsed'].dt.day_name()

# Extract numeric day (0=Monday, 6=Sunday) for analysis
df['day_num'] = df['injury_date_parsed'].dt.dayofweek
```

## Verification

All 8,497 records parsed successfully (100% success rate). Sample verification:

| injury_date | Parsed Date | Day of Week | Player | Injury Type |
|-------------|-------------|-------------|--------|-------------|
| May 6, 2019 | 2019-05-06 | Monday | Donovan Pines | Knee injury |
| Apr 1, 2024 | 2024-04-01 | Monday | Andre Blake | Concussion |
| Oct 14, 2020 | 2020-10-14 | Wednesday | Cristian Olivera | Unknown injury |
| May 18, 2025 | 2025-05-18 | Sunday | Andrés Perea | Leg injury |
| Mar 8, 2025 | 2025-03-08 | Saturday | Maximiliano Falcón | Shoulder injury |

Calendar verification confirms pandas parsing accuracy.

## Results

### Day-of-Week Distribution (All 8,497 Injuries)

| Day | Count | Percentage | Notes |
|-----|-------|------------|-------|
| **Monday** | **2,142** | **25.2%** | **Highest single day** |
| Tuesday | 932 | 11.0% | |
| Wednesday | 927 | 10.9% | Typical MLS match day |
| **Thursday** | **1,484** | **17.5%** | **Second highest** |
| Friday | 1,330 | 15.7% | |
| Saturday | 791 | 9.3% | Typical MLS match day |
| Sunday | 891 | 10.5% | Typical MLS match day |

### Match Day vs. Day-After Analysis

**Match Days** (Wed/Sat/Sun): 2,609 injuries (30.7%)
**Day-After Match** (Mon/Thu): 3,626 injuries (42.7%)
**Ratio**: 1.39x more injuries reported day-after vs. during matches

**48-Hour Match Window** (Wed/Thu/Sat/Sun/Mon): 6,235 injuries (73.4%)

## Critical Limitation: Reporting Dates vs. Occurrence Dates

### What the Data Actually Represents

The `injury_date` field from Transfermarkt.us represents **when the injury was reported/documented**, not necessarily when the physical injury occurred.

### Example Timeline

**Scenario 1: Acute Match Injury**
- Saturday 3:00 PM: Player collides with opponent, knee buckles
- Saturday 3:15 PM: Player exits match, medical evaluation
- Saturday 6:00 PM: Team announces injury, media reports
- Saturday-Sunday: Transfermarkt updates database
- **injury_date: Saturday** ✓ Accurate

**Scenario 2: Delayed-Onset Injury**
- Saturday 3:00 PM: Player completes 90 minutes, feels slight hamstring tightness
- Saturday evening: Player ices, takes anti-inflammatories
- Sunday: Muscle soreness increases, player reports to medical staff
- Monday 9:00 AM: MRI reveals Grade 2 hamstring strain
- Monday 11:00 AM: Team places player on injury list, announces to media
- Monday-Tuesday: Transfermarkt updates database
- **injury_date: Monday** ← Reported 2 days after actual tissue damage

### Implications for Analysis

**What we CAN conclude:**
1. ✅ Injuries are reported/discovered more frequently on Mondays (25.2%) and Thursdays (17.5%) than any other days
2. ✅ This pattern is consistent with post-match medical evaluations and delayed-onset muscle soreness
3. ✅ The day-after spike (42.7%) exceeds match-day reporting (30.7%) by a significant margin
4. ✅ This suggests many injuries are not immediately apparent during matches

**What we CANNOT conclude:**
1. ❌ The exact moment tissue damage occurred
2. ❌ Whether the injury happened during a match, training, or off-field activity
3. ❌ The precise lag time between injury occurrence and reporting (varies by team, injury type)

**Why the pattern is still meaningful:**
- Acute traumatic injuries (ACL tears from collisions, fractures, dislocations) are almost always identified immediately and reported on game day
- The fact that Monday/Thursday dominate suggests a large proportion of injuries are NOT acute trauma
- Delayed reporting indicates delayed discovery, which implies injuries that develop or become apparent over time
- This is consistent with overuse injuries, muscle strains, and cumulative stress injuries—exactly the types expected from fixture congestion

### Validation Against Match Schedules

MLS typical match schedule:
- **Wednesday**: Midweek matches (secondary)
- **Saturday**: Primary match day
- **Sunday**: Primary match day

If all injuries occurred during matches and were reported same-day, we'd expect:
- Wed/Sat/Sun combined: ~70-80% of injuries
- Mon/Thu combined: ~5-10% of injuries

**Actual distribution:**
- Wed/Sat/Sun: 30.7% (far lower than expected)
- Mon/Thu: 42.7% (far higher than expected)

This divergence supports the interpretation that many injuries surface after matches rather than during them.

## Comparison to Peer-Reviewed Research

The MLS Injury Surveillance Database (2010-2021) tracks injuries by match vs. training occurrence but does not publish day-of-week patterns. However, research on muscle injuries consistently shows:

1. **Delayed-onset muscle soreness (DOMS)** peaks 24-72 hours post-exercise[^1]
2. **Muscle strain diagnosis** often occurs 1-2 days after the precipitating event when swelling/pain becomes apparent
3. **Post-match injury evaluation protocols** in professional soccer typically occur the day after matches

The Monday/Thursday spike is consistent with these known biomechanical and clinical patterns.

## Transparency Statement for Article

The article methodology section includes this disclosure:

> "Injury timing analyzed by day of week based on reported injury dates from Transfermarkt.us. Note: These dates represent when injuries were documented/reported, not necessarily when they occurred, meaning the day-of-week pattern captures injury discovery and reporting timing (acute match injuries typically reported same day; delayed-onset injuries surface 1-2 days later)."

## Recommended Interpretation

The day-of-week pattern is best interpreted as:

1. **A proxy for injury discovery timing** - not exact occurrence timing
2. **Evidence of delayed-onset injury patterns** - supporting the fixture congestion hypothesis
3. **An indicator of recovery protocol gaps** - players are not identifying/reporting issues until they worsen
4. **Consistent with overuse injury mechanisms** - as opposed to acute traumatic injuries

The 42.7% Monday/Thursday concentration strongly suggests inadequate recovery windows between matches, as this is when accumulated stress manifests as diagnosable injuries.

---

## References

[^1]: Cheung K, Hume PA, Maxwell L. "Delayed onset muscle soreness: treatment strategies and performance factors." *Sports Med*, 2003;33(2):145-164. PMID: 12617692.

---

*Technical documentation for "MLS's Injury Crisis: Why Players Are Breaking Down at Unprecedented Rates"*
