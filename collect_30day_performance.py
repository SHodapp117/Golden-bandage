#!/usr/bin/env python3
"""
Collect player performance data 30 days before and after each injury
Uses Transfermarkt match-by-match performance data
"""

import requests
from bs4 import BeautifulSoup
import pandas as pd
import time
from datetime import datetime, timedelta
import logging
from tqdm import tqdm

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class Performance30DayCollector:
    """Collects performance data 30 days before/after injuries"""

    BASE_URL = "https://www.transfermarkt.us"

    def __init__(self, delay: float = 3.0):
        self.delay = delay
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36'
        })

    def _get_page(self, url: str):
        """Fetch page with rate limiting"""
        try:
            time.sleep(self.delay)
            response = self.session.get(url, timeout=10)
            response.raise_for_status()
            return BeautifulSoup(response.content, 'html.parser')
        except Exception as e:
            logger.error(f"Failed to fetch {url}: {e}")
            return None

    def parse_date(self, date_str: str):
        """Parse various date formats from Transfermarkt"""
        try:
            # Try "Mon DD, YYYY" format
            return datetime.strptime(date_str, '%b %d, %Y')
        except:
            try:
                # Try other common formats
                return pd.to_datetime(date_str)
            except:
                return None

    def get_match_performance_data(self, player_url: str, season: str):
        """
        Get game-by-game performance data for a player in a season

        Returns list of matches with dates and stats
        """
        # Build performance detail URL
        perf_url = player_url.replace('/profil/', '/leistungsdatendetails/')
        perf_url += f"/saison/{season}/plus/1"  # plus/1 gives detailed match view

        soup = self._get_page(perf_url)
        if not soup:
            return []

        matches = []

        # Find the performance table
        perf_table = soup.find('table', {'class': 'items'})
        if not perf_table:
            return []

        rows = perf_table.find_all('tr', {'class': ['odd', 'even']})

        for row in rows:
            cells = row.find_all('td')
            if len(cells) < 10:
                continue

            try:
                # Extract match date
                date_cell = cells[2]
                date_str = date_cell.text.strip()
                match_date = self.parse_date(date_str)

                if not match_date:
                    continue

                # Extract stats
                # Position in lineup (started/sub)
                position_cell = cells[3]
                started = 'Startaufstellung' in position_cell.get('title', '') or \
                         position_cell.find('span', {'class': 'hauptposition'}) is not None

                # Minutes played
                minutes_cell = cells[5]
                minutes_text = minutes_cell.text.strip().replace("'", "")
                minutes = int(minutes_text) if minutes_text.isdigit() else 0

                # Goals
                goals_cell = cells[6]
                goals = int(goals_cell.text.strip()) if goals_cell.text.strip().isdigit() else 0

                # Assists
                assists_cell = cells[7]
                assists = int(assists_cell.text.strip()) if assists_cell.text.strip().isdigit() else 0

                # Yellow/Red cards
                yellow_cell = cells[8]
                yellow = 1 if yellow_cell.find('div', {'class': 'yellow-card'}) else 0

                red_cell = cells[9]
                red = 1 if red_cell.find('div', {'class': 'red-card'}) else 0

                matches.append({
                    'date': match_date,
                    'started': started,
                    'minutes': minutes,
                    'goals': goals,
                    'assists': assists,
                    'yellow_cards': yellow,
                    'red_cards': red
                })

            except Exception as e:
                logger.debug(f"Error parsing match row: {e}")
                continue

        return matches

    def calculate_30day_stats(self, injury_date_str: str, player_url: str):
        """
        Calculate stats for 30 days before and after injury

        Returns: (before_stats, after_stats)
        """
        injury_date = self.parse_date(injury_date_str)
        if not injury_date:
            return {}, {}

        # Determine which season(s) to check
        injury_year = injury_date.year

        # MLS season typically runs Feb-Oct, but check both current and adjacent years
        seasons_to_check = []

        # For dates in Jan-Jun, check previous year's season
        if injury_date.month <= 6:
            seasons_to_check.append(str(injury_year - 1))

        # Always check current year
        seasons_to_check.append(str(injury_year))

        # For dates in Jul-Dec, also check next year
        if injury_date.month >= 7:
            seasons_to_check.append(str(injury_year + 1))

        # Collect all matches from relevant seasons
        all_matches = []
        for season in seasons_to_check:
            matches = self.get_match_performance_data(player_url, season)
            all_matches.extend(matches)

        # Define time windows
        window_before_start = injury_date - timedelta(days=30)
        window_before_end = injury_date

        window_after_start = injury_date
        window_after_end = injury_date + timedelta(days=30)

        # Filter matches into before/after windows
        matches_before = [
            m for m in all_matches
            if window_before_start <= m['date'] < window_before_end
        ]

        matches_after = [
            m for m in all_matches
            if window_after_start < m['date'] <= window_after_end
        ]

        # Aggregate stats
        def aggregate_matches(matches):
            if not matches:
                return {
                    'games': 0,
                    'games_started': 0,
                    'minutes': 0,
                    'goals': 0,
                    'assists': 0,
                    'yellow_cards': 0,
                    'red_cards': 0,
                    'performance_score': 0.0
                }

            stats = {
                'games': len(matches),
                'games_started': sum(1 for m in matches if m['started']),
                'minutes': sum(m['minutes'] for m in matches),
                'goals': sum(m['goals'] for m in matches),
                'assists': sum(m['assists'] for m in matches),
                'yellow_cards': sum(m['yellow_cards'] for m in matches),
                'red_cards': sum(m['red_cards'] for m in matches)
            }

            # Calculate performance score (goals + assists per 90 minutes)
            if stats['minutes'] > 0:
                stats['performance_score'] = round(
                    (stats['goals'] + stats['assists']) * 90 / stats['minutes'],
                    3
                )
            else:
                stats['performance_score'] = 0.0

            return stats

        before_stats = aggregate_matches(matches_before)
        after_stats = aggregate_matches(matches_after)

        # Add prefix to keys
        before_stats = {f'before_{k}': v for k, v in before_stats.items()}
        after_stats = {f'after_{k}': v for k, v in after_stats.items()}

        return before_stats, after_stats

    def enhance_injury_dataset(
        self,
        input_csv: str = "mls_player_injuries.csv",
        output_csv: str = "mls_player_injuries_30day_performance.csv"
    ):
        """
        Enhance injury dataset with 30-day performance windows
        """
        logger.info(f"Loading injury data from {input_csv}")
        df = pd.read_csv(input_csv)

        logger.info(f"Enhancing {len(df)} injury records with 30-day performance data")

        # Add new columns
        new_cols = [
            'before_games', 'before_games_started', 'before_minutes',
            'before_goals', 'before_assists', 'before_yellow_cards',
            'before_red_cards', 'before_performance_score',
            'after_games', 'after_games_started', 'after_minutes',
            'after_goals', 'after_assists', 'after_yellow_cards',
            'after_red_cards', 'after_performance_score'
        ]

        for col in new_cols:
            df[col] = None

        # Process each injury with progress bar
        for idx in tqdm(range(len(df)), desc="Processing injuries"):
            row = df.iloc[idx]

            before_stats, after_stats = self.calculate_30day_stats(
                row['injury_date'],
                row['player_url']
            )

            # Update dataframe
            for key, value in before_stats.items():
                df.at[idx, key] = value

            for key, value in after_stats.items():
                df.at[idx, key] = value

        # Save enhanced dataset
        df.to_csv(output_csv, index=False)
        logger.info(f"Saved enhanced dataset to {output_csv}")

        # Print summary
        print("\n" + "="*70)
        print("ENHANCEMENT SUMMARY")
        print("="*70)
        print(f"Total records: {len(df):,}")
        print(f"Records with pre-injury data: {df['before_games'].notna().sum():,}")
        print(f"Records with post-injury data: {df['after_games'].notna().sum():,}")
        print(f"\nAverage games before injury: {df['before_games'].mean():.2f}")
        print(f"Average games after injury: {df['after_games'].mean():.2f}")
        print(f"\nAverage performance before: {df['before_performance_score'].mean():.3f}")
        print(f"Average performance after: {df['after_performance_score'].mean():.3f}")
        print("="*70)

        return df


def main():
    """Main execution"""
    print("="*70)
    print("MLS Injury Data - 30-Day Performance Enhancement")
    print("="*70)
    print("\nThis will collect player performance data for:")
    print("  - 30 days BEFORE each injury")
    print("  - 30 days AFTER each injury")
    print("\nEstimated time: 6-10 hours (3 sec delay per injury)")
    print("="*70)

    collector = Performance30DayCollector(delay=3.0)
    df = collector.enhance_injury_dataset()


if __name__ == "__main__":
    main()
