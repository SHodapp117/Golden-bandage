#!/usr/bin/env python3
"""
MLS Injury Data Scraper
Collects historical injury data for MLS players from Transfermarkt
"""

import requests
from bs4 import BeautifulSoup
import pandas as pd
import time
from datetime import datetime
import csv
import re
from typing import List, Dict, Optional, Set
import logging
from tqdm import tqdm
import os
import json

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class TransfermarktScraper:
    """Scraper for Transfermarkt MLS injury data"""

    BASE_URL = "https://www.transfermarkt.us"
    MLS_LEAGUE_URL = f"{BASE_URL}/major-league-soccer/startseite/wettbewerb/MLS1"

    def __init__(self, delay: float = 2.0, checkpoint_file: str = "scraper_checkpoint.json"):
        """
        Initialize scraper with rate limiting

        Args:
            delay: Seconds to wait between requests (default 2.0)
            checkpoint_file: File to store progress checkpoints
        """
        self.delay = delay
        self.checkpoint_file = checkpoint_file
        self.processed_players: Set[str] = set()  # Hash set for O(1) lookup
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36'
        })
        self._load_checkpoint()

    def _load_checkpoint(self):
        """Load progress from checkpoint file if it exists"""
        if os.path.exists(self.checkpoint_file):
            try:
                with open(self.checkpoint_file, 'r') as f:
                    data = json.load(f)
                    self.processed_players = set(data.get('processed_players', []))
                    logger.info(f"Resumed from checkpoint: {len(self.processed_players)} players already processed")
            except Exception as e:
                logger.warning(f"Could not load checkpoint: {e}")
                self.processed_players = set()

    def _load_processed_from_csv(self, output_file: str):
        """Load already-processed players from existing CSV to prevent duplicates"""
        if os.path.exists(output_file):
            try:
                df = pd.read_csv(output_file)
                # Create unique keys from existing data
                for _, row in df.iterrows():
                    # Use player_url + season as key (assumes these columns exist)
                    if 'player_url' in df.columns and 'season' in df.columns:
                        player_key = f"{row['player_url']}_{row['season']}"
                        self.processed_players.add(player_key)
                logger.info(f"Loaded {len(self.processed_players)} players from existing CSV")
            except Exception as e:
                logger.warning(f"Could not load from CSV: {e}")

    def _save_checkpoint(self):
        """Save current progress to checkpoint file"""
        try:
            with open(self.checkpoint_file, 'w') as f:
                json.dump({
                    'processed_players': list(self.processed_players),
                    'last_updated': datetime.now().isoformat()
                }, f)
        except Exception as e:
            logger.warning(f"Could not save checkpoint: {e}")

    def _get_page(self, url: str) -> Optional[BeautifulSoup]:
        """
        Fetch and parse a webpage with rate limiting

        Args:
            url: URL to fetch

        Returns:
            BeautifulSoup object or None if failed
        """
        try:
            time.sleep(self.delay)  # Rate limiting
            response = self.session.get(url, timeout=10)
            response.raise_for_status()
            return BeautifulSoup(response.content, 'html.parser')
        except Exception as e:
            logger.error(f"Failed to fetch {url}: {e}")
            return None

    def get_mls_teams(self, season: str = "2024") -> List[Dict[str, str]]:
        """
        Get all MLS teams for a given season

        Args:
            season: Season year (e.g., "2024")

        Returns:
            List of team dictionaries with name and URL
        """
        url = f"{self.MLS_LEAGUE_URL}/plus/?saison_id={season}"
        soup = self._get_page(url)

        if not soup:
            return []

        teams = []
        # Find team table
        team_table = soup.find('table', {'class': 'items'})
        if team_table:
            for row in team_table.find_all('tr', {'class': ['odd', 'even']}):
                team_cell = row.find('td', {'class': 'hauptlink'})
                if team_cell and team_cell.find('a'):
                    team_link = team_cell.find('a')
                    teams.append({
                        'name': team_link.text.strip(),
                        'url': self.BASE_URL + team_link['href']
                    })

        logger.info(f"Found {len(teams)} MLS teams for {season}")
        return teams

    def get_team_players(self, team_url: str, season: str = "2024") -> List[Dict[str, str]]:
        """
        Get all players for a specific team

        Args:
            team_url: URL of the team page
            season: Season year (e.g., "2024")

        Returns:
            List of player dictionaries
        """
        # Convert team homepage URL to squad/kader page
        # Example: /inter-miami-cf/startseite/verein/69012 -> /inter-miami-cf/kader/verein/69012/saison_id/2024
        squad_url = team_url.replace('/startseite/', '/kader/') + f"/saison_id/{season}/plus/1"

        soup = self._get_page(squad_url)

        if not soup:
            return []

        players = []
        # Find player table
        player_table = soup.find('table', {'class': 'items'})
        if player_table:
            for row in player_table.find_all('tr', {'class': ['odd', 'even']}):
                # Get player name and URL from the positionCell
                cells = row.find_all('td')
                if len(cells) > 1:
                    # Position is typically in the second cell
                    position_cell = cells[0] if len(cells) > 0 else None
                    position = ""
                    if position_cell:
                        # Position might be in a nested table or div
                        pos_text = position_cell.get_text(strip=True)
                        position = pos_text if pos_text else "Unknown"

                    # Player name is in hauptlink cell
                    name_cell = row.find('td', {'class': 'hauptlink'})
                    if name_cell:
                        player_links = name_cell.find_all('a')
                        for link in player_links:
                            if '/profil/spieler/' in link.get('href', ''):
                                players.append({
                                    'name': link.text.strip(),
                                    'url': self.BASE_URL + link['href'],
                                    'position': position
                                })
                                break

        logger.info(f"Found {len(players)} players")
        return players

    def get_player_injuries(self, player_url: str, player_name: str, position: str, team: str) -> List[Dict]:
        """
        Get injury history for a specific player

        Args:
            player_url: URL of the player page
            player_name: Name of the player
            position: Player position
            team: Player team

        Returns:
            List of injury dictionaries
        """
        # Convert player profile URL to injury page URL
        injury_url = player_url.replace('/profil/', '/verletzungen/')
        soup = self._get_page(injury_url)

        if not soup:
            return []

        injuries = []
        # Find injury table
        injury_table = soup.find('table', {'class': 'items'})
        if injury_table:
            for row in injury_table.find_all('tr', {'class': ['odd', 'even']}):
                cells = row.find_all('td')
                if len(cells) >= 5:
                    try:
                        season = cells[0].text.strip()
                        injury_type = cells[1].text.strip()
                        date_from = cells[2].text.strip()
                        date_until = cells[3].text.strip()
                        days_out = cells[4].text.strip()
                        games_missed = cells[5].text.strip() if len(cells) > 5 else "N/A"

                        # Extract numeric days
                        days_match = re.search(r'(\d+)', days_out)
                        days_numeric = int(days_match.group(1)) if days_match else None

                        # Extract numeric games
                        games_match = re.search(r'(\d+)', games_missed)
                        games_numeric = int(games_match.group(1)) if games_match else None

                        injuries.append({
                            'player_name': player_name,
                            'position': position,
                            'team': team,
                            'season': season,
                            'injury_type': injury_type,
                            'injury_date': date_from,
                            'return_date': date_until,
                            'days_out': days_numeric,
                            'games_missed': games_numeric,
                            'player_url': player_url,
                            'data_collection_date': datetime.now().strftime('%Y-%m-%d')
                        })
                    except Exception as e:
                        logger.warning(f"Error parsing injury row for {player_name}: {e}")

        if injuries:
            logger.info(f"Found {len(injuries)} injuries for {player_name}")

        return injuries

    def scrape_mls_injuries(self, seasons: List[str] = None, output_file: str = "mls_player_injuries.csv") -> pd.DataFrame:
        """
        Scrape injury data for all MLS players across multiple seasons

        Args:
            seasons: List of season years (e.g., ["2020", "2021", "2022"])
            output_file: CSV file to save results

        Returns:
            DataFrame with all injury data
        """
        if seasons is None:
            # Default to recent seasons
            seasons = ["2019", "2020", "2021", "2022", "2023", "2024"]

        # Check if output file exists and load existing data
        file_exists = os.path.exists(output_file)
        write_header = not file_exists

        # Load players from CSV to prevent duplicates across runs
        self._load_processed_from_csv(output_file)

        # Progress bar for seasons
        for season in tqdm(seasons, desc="Seasons", position=0):
            logger.info(f"Processing season {season}")
            teams = self.get_mls_teams(season)

            # Progress bar for teams
            for team in tqdm(teams, desc=f"Teams ({season})", position=1, leave=False):
                logger.info(f"Processing team: {team['name']}")
                players = self.get_team_players(team['url'], season)

                # Progress bar for players
                for player in tqdm(players, desc=f"{team['name'][:20]}", position=2, leave=False):
                    # Create unique player key using URL (most reliable identifier)
                    player_key = f"{player['url']}_{season}"

                    # Skip if already processed (O(1) lookup with hash set)
                    if player_key in self.processed_players:
                        logger.debug(f"Skipping already processed player: {player['name']}")
                        continue

                    injuries = self.get_player_injuries(
                        player['url'],
                        player['name'],
                        player['position'],
                        team['name']
                    )

                    # Mark player as processed
                    self.processed_players.add(player_key)

                    # Incremental write to CSV to prevent data loss
                    if injuries:
                        df_batch = pd.DataFrame(injuries)
                        df_batch.to_csv(
                            output_file,
                            mode='a',
                            header=write_header,
                            index=False
                        )
                        write_header = False  # Only write header once

                    # Save checkpoint every 10 players
                    if len(self.processed_players) % 10 == 0:
                        self._save_checkpoint()

                # Extra delay between teams to be respectful
                time.sleep(self.delay)

        # Final checkpoint save
        self._save_checkpoint()

        # Read final CSV
        if os.path.exists(output_file):
            df = pd.read_csv(output_file)
            print(f"\n✓ Saved {len(df)} injury records to {output_file}")
            logger.info(f"Saved {len(df)} injury records to {output_file}")
            return df
        else:
            print("\n✗ No injury data collected")
            return pd.DataFrame()


def main():
    """Main execution function"""
    print("="*70)
    print("MLS Injury Data Collection")
    print("="*70)

    scraper = TransfermarktScraper(delay=3.0)  # 3 second delay to be respectful

    # Scrape injuries from 2015-2024 (longest possible span)
    seasons = [str(year) for year in range(2015, 2025)]

    print(f"\nCollecting data for seasons: {', '.join(seasons)}")
    print(f"Estimated runtime: 3-7 hours")
    print(f"Rate limit: 3 seconds between requests\n")

    logger.info("Starting MLS injury data collection...")
    logger.info(f"Seasons: {', '.join(seasons)}")

    df = scraper.scrape_mls_injuries(
        seasons=seasons,
        output_file="mls_player_injuries.csv"
    )

    if not df.empty:
        print("\n" + "="*70)
        print("COLLECTION SUMMARY")
        print("="*70)
        print(f"✓ Total injuries collected: {len(df)}")
        print(f"✓ Unique players: {df['player_name'].nunique()}")
        print(f"✓ Date range: {df['injury_date'].min()} to {df['injury_date'].max()}")
        print(f"\nTop 10 injury types:")
        print(df['injury_type'].value_counts().head(10).to_string())
        print("="*70)

        logger.info("\n=== Collection Summary ===")
        logger.info(f"Total injuries collected: {len(df)}")
        logger.info(f"Unique players: {df['player_name'].nunique()}")
        logger.info(f"Date range: {df['injury_date'].min()} to {df['injury_date'].max()}")
    else:
        print("\n✗ No injury data collected")
        logger.warning("No injury data collected")


if __name__ == "__main__":
    main()
