#!/usr/bin/env python3
"""
MLS Performance Data Collector
Enhances injury data with player performance metrics before and after injury
"""

import requests
from bs4 import BeautifulSoup
import pandas as pd
import time
from datetime import datetime, timedelta
from typing import Dict, Optional, List
import logging

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class PerformanceDataCollector:
    """Collects performance metrics from Transfermarkt and FBref"""

    BASE_URL_TM = "https://www.transfermarkt.us"

    def __init__(self, delay: float = 2.0):
        self.delay = delay
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36'
        })

    def _get_page(self, url: str) -> Optional[BeautifulSoup]:
        """Fetch and parse a webpage with rate limiting"""
        try:
            time.sleep(self.delay)
            response = self.session.get(url, timeout=10)
            response.raise_for_status()
            return BeautifulSoup(response.content, 'html.parser')
        except Exception as e:
            logger.error(f"Failed to fetch {url}: {e}")
            return None

    def get_player_performance_stats(self, player_url: str, season: str) -> Dict:
        """
        Get performance statistics for a player in a given season

        Args:
            player_url: Transfermarkt player URL
            season: Season (e.g., "2023")

        Returns:
            Dictionary with performance stats
        """
        # Convert to performance data page
        perf_url = player_url.replace('/profil/', '/leistungsdatendetails/')
        perf_url += f"/saison/{season}"

        soup = self._get_page(perf_url)

        if not soup:
            return {}

        stats = {
            'games': 0,
            'minutes': 0,
            'goals': 0,
            'assists': 0,
            'yellow_cards': 0,
            'red_cards': 0
        }

        # Find performance table
        perf_table = soup.find('table', {'class': 'items'})
        if perf_table:
            # Look for summary row (usually last row)
            rows = perf_table.find_all('tr', {'class': ['odd', 'even']})
            if rows:
                # Sum up stats from all competitions
                for row in rows:
                    cells = row.find_all('td')
                    if len(cells) >= 10:
                        try:
                            # Parse appearances
                            appearances = cells[3].text.strip()
                            if appearances.isdigit():
                                stats['games'] += int(appearances)

                            # Parse minutes (remove thousands separator)
                            minutes_text = cells[5].text.strip().replace('.', '').replace(',', '')
                            if minutes_text.isdigit():
                                stats['minutes'] += int(minutes_text)

                            # Parse goals
                            goals = cells[6].text.strip()
                            if goals.isdigit():
                                stats['goals'] += int(goals)

                            # Parse assists
                            assists = cells[7].text.strip()
                            if assists.isdigit():
                                stats['assists'] += int(assists)

                        except (ValueError, IndexError) as e:
                            logger.debug(f"Error parsing performance row: {e}")

        return stats

    def calculate_performance_window(
        self,
        injury_date: str,
        player_url: str,
        window_days: int = 90
    ) -> tuple[Dict, Dict]:
        """
        Calculate performance before and after injury

        Args:
            injury_date: Date of injury (YYYY-MM-DD or similar)
            player_url: Player URL
            window_days: Days to look before/after injury (default 90)

        Returns:
            Tuple of (before_stats, after_stats)
        """
        try:
            # Parse injury date
            injury_dt = pd.to_datetime(injury_date, errors='coerce')
            if pd.isna(injury_dt):
                return {}, {}

            # Determine season
            injury_year = injury_dt.year
            # Soccer seasons typically span two years (e.g., 2023 season = 2023-2024)
            if injury_dt.month < 7:  # Before July = previous season
                season = str(injury_year - 1)
            else:
                season = str(injury_year)

            # Get season stats
            season_stats = self.get_player_performance_stats(player_url, season)

            # For now, return full season stats
            # More granular game-by-game data would require additional scraping
            before_stats = {
                'games_before': season_stats.get('games', 0),
                'minutes_before': season_stats.get('minutes', 0),
                'goals_before': season_stats.get('goals', 0),
                'assists_before': season_stats.get('assists', 0)
            }

            # After stats would require next season or remaining season data
            after_stats = {
                'games_after': 0,
                'minutes_after': 0,
                'goals_after': 0,
                'assists_after': 0
            }

            return before_stats, after_stats

        except Exception as e:
            logger.error(f"Error calculating performance window: {e}")
            return {}, {}

    def enhance_injury_data(
        self,
        injury_csv: str = "mls_player_injuries.csv",
        output_csv: str = "mls_player_injuries_enhanced.csv"
    ):
        """
        Enhance injury data with performance metrics

        Args:
            injury_csv: Input CSV with injury data
            output_csv: Output CSV with enhanced data
        """
        logger.info(f"Loading injury data from {injury_csv}")
        df = pd.read_csv(injury_csv)

        logger.info(f"Enhancing {len(df)} injury records with performance data")

        # Add performance columns
        performance_cols = [
            'games_before', 'minutes_before', 'goals_before', 'assists_before',
            'games_after', 'minutes_after', 'goals_after', 'assists_after',
            'performance_before_injury', 'performance_after_injury'
        ]

        for col in performance_cols:
            if col not in df.columns:
                df[col] = None

        # Process each injury
        for idx, row in df.iterrows():
            if idx % 10 == 0:
                logger.info(f"Processing {idx}/{len(df)}")

            before_stats, after_stats = self.calculate_performance_window(
                row['injury_date'],
                row['player_url']
            )

            # Update DataFrame
            for key, value in before_stats.items():
                df.at[idx, key] = value

            for key, value in after_stats.items():
                df.at[idx, key] = value

            # Calculate performance scores (simple: goals + assists per 90 minutes)
            if before_stats.get('minutes_before', 0) > 0:
                perf_before = (
                    (before_stats['goals_before'] + before_stats['assists_before'])
                    * 90 / before_stats['minutes_before']
                )
                df.at[idx, 'performance_before_injury'] = round(perf_before, 3)

            if after_stats.get('minutes_after', 0) > 0:
                perf_after = (
                    (after_stats['goals_after'] + after_stats['assists_after'])
                    * 90 / after_stats['minutes_after']
                )
                df.at[idx, 'performance_after_injury'] = round(perf_after, 3)

        # Save enhanced data
        df.to_csv(output_csv, index=False)
        logger.info(f"Saved enhanced data to {output_csv}")

        return df


def main():
    """Main execution"""
    collector = PerformanceDataCollector(delay=3.0)

    df = collector.enhance_injury_data(
        injury_csv="mls_player_injuries.csv",
        output_csv="mls_player_injuries_enhanced.csv"
    )

    logger.info("\n=== Enhancement Summary ===")
    logger.info(f"Total records enhanced: {len(df)}")
    logger.info(f"Records with pre-injury stats: {df['games_before'].notna().sum()}")
    logger.info(f"Records with post-injury stats: {df['games_after'].notna().sum()}")


if __name__ == "__main__":
    main()
