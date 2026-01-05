#!/usr/bin/env python3
"""
Match injuries to actual match fixtures to determine stadium location
Cross-references injury date with team's schedule to find if home/away
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


class FixtureMatchingService:
    """Matches injuries to fixtures to determine actual stadium location"""

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

    def get_team_fixtures(self, team_name: str, season: str):
        """
        Get all fixtures for a team in a season

        Returns list of matches with:
        - date
        - opponent
        - home_team (who hosted the match)
        - stadium (where it was played)
        """
        # Build team fixtures URL
        # Example: /seattle-sounders-fc/spielplan/verein/9726/saison_id/2023

        # First need to get team ID from team name
        team_id = self._get_team_id(team_name)
        if not team_id:
            return []

        fixtures_url = f"{self.BASE_URL}/{team_name.lower().replace(' ', '-')}/spielplan/verein/{team_id}/saison_id/{season}"

        soup = self._get_page(fixtures_url)
        if not soup:
            return []

        fixtures = []

        # Find fixture table
        fixture_table = soup.find('table', {'class': 'items'})
        if not fixture_table:
            return []

        rows = fixture_table.find_all('tr', {'class': ['odd', 'even']})

        for row in rows:
            try:
                cells = row.find_all('td')
                if len(cells) < 8:
                    continue

                # Extract date
                date_cell = cells[1]
                date_str = date_cell.text.strip()
                match_date = self._parse_date(date_str)

                if not match_date:
                    continue

                # Extract opponent and home/away status
                home_team_cell = cells[4]
                away_team_cell = cells[6]

                home_team = home_team_cell.find('a', {'class': 'vereinprofil_tooltip'})
                away_team = away_team_cell.find('a', {'class': 'vereinprofil_tooltip'})

                if not home_team or not away_team:
                    continue

                home_team_name = home_team['title']
                away_team_name = away_team['title']

                # Determine if our team was home or away
                is_home = (home_team_name == team_name)
                opponent = away_team_name if is_home else home_team_name

                fixtures.append({
                    'date': match_date,
                    'opponent': opponent,
                    'home_team': home_team_name,
                    'away_team': away_team_name,
                    'is_home_game': is_home
                })

            except Exception as e:
                logger.debug(f"Error parsing fixture row: {e}")
                continue

        return fixtures

    def _get_team_id(self, team_name: str):
        """Get Transfermarkt team ID from team name"""
        team_ids = {
            # Current MLS Teams (2025)
            'Atlanta United FC': '37326',
            'Austin FC': '77715',
            'Charlotte FC': '91117',
            'Chicago Fire FC': '3962',
            'FC Cincinnati': '41012',
            'Colorado Rapids': '3963',
            'Columbus Crew': '3966',
            'D.C. United': '3967',
            'FC Dallas': '3969',
            'Houston Dynamo FC': '8006',
            'Inter Miami CF': '69220',
            'LA Galaxy': '3964',
            'Los Angeles FC': '51923',
            'Minnesota United FC': '31614',
            'CF Montréal': '3976',
            'Nashville SC': '70869',
            'New England Revolution': '3977',
            'New York City FC': '28171',
            'New York Red Bulls': '3979',
            'Orlando City SC': '22309',
            'Philadelphia Union': '10316',
            'Portland Timbers': '9721',
            'Real Salt Lake': '3982',
            'San Jose Earthquakes': '3983',
            'Seattle Sounders FC': '9726',
            'Sporting Kansas City': '3984',
            'St. Louis City SC': '105220',
            'Toronto FC': '5204',
            'Vancouver Whitecaps FC': '10139',

            # Defunct/Relocated MLS Teams
            'Chivas USA': '4021',

            # Alternative name variations and historical names
            'Montréal Impact': '3976',  # Same as CF Montréal
            'Montreal Impact': '3976',
            'Sporting KC': '3984',  # Same as Sporting Kansas City
            'Real Salt Lake City': '3982',  # Same as Real Salt Lake
            'St. Louis CITY SC': '105220',  # Same as St. Louis City SC
            'Chicago Fire': '3962',  # Old name for Chicago Fire FC
            'Columbus Crew SC': '3966',  # Old name for Columbus Crew
            'Houston Dynamo': '8006',  # Old name for Houston Dynamo FC
            'FC Montréal': '3976',  # Another variation
        }

        # Try to match, if not found log warning
        team_id = team_ids.get(team_name)
        if not team_id:
            logger.debug(f"No team ID found for: {team_name}")
        return team_id

    def _parse_date(self, date_str: str):
        """Parse various date formats"""
        try:
            return datetime.strptime(date_str, '%b %d, %Y')
        except:
            try:
                return pd.to_datetime(date_str)
            except:
                return None

    def find_match_for_injury(self, injury_date_str: str, team_name: str, season: str):
        """
        Find the match that corresponds to an injury date

        Returns:
        - home_team: Which team hosted (determines stadium)
        - opponent: Who they were playing
        - match_date: Actual match date
        - days_diff: Days between injury and nearest match
        """
        injury_date = self._parse_date(injury_date_str)
        if not injury_date:
            return None

        # Get all fixtures for the season
        fixtures = self.get_team_fixtures(team_name, season)

        if not fixtures:
            return None

        # Find closest match (within 7 days before injury date)
        closest_match = None
        min_diff = float('inf')

        for fixture in fixtures:
            # Calculate days between match and injury
            diff = (injury_date - fixture['date']).days

            # Only consider matches within 7 days BEFORE injury
            # (injuries happen during/after matches, not before)
            if 0 <= diff <= 7 and diff < min_diff:
                min_diff = diff
                closest_match = fixture

        if closest_match:
            return {
                'match_date': closest_match['date'],
                'home_team': closest_match['home_team'],
                'away_team': closest_match['away_team'],
                'opponent': closest_match['opponent'],
                'is_home_game': closest_match['is_home_game'],
                'days_between_match_and_injury': min_diff
            }

        return None

    def enhance_injuries_with_fixtures(
        self,
        input_csv: str = "mls_player_injuries.csv",
        stadiums_csv: str = "mls_stadiums.csv",
        output_csv: str = "mls_injuries_fixture_matched.csv"
    ):
        """
        Enhance injury data by matching to actual fixtures
        Determines where injury occurred based on home team
        """
        logger.info(f"Loading injury data from {input_csv}")
        injuries = pd.read_csv(input_csv)

        logger.info(f"Loading stadium data from {stadiums_csv}")
        stadiums = pd.read_csv(stadiums_csv)

        # Add fixture-based columns
        new_cols = [
            'match_date', 'home_team', 'away_team', 'opponent',
            'is_home_game', 'days_between_match_and_injury',
            'stadium_name', 'surface_type', 'city', 'state',
            'altitude_ft', 'climate_zone'
        ]

        for col in new_cols:
            injuries[col] = None

        # Extract injury year for season lookup
        injuries['injury_year'] = pd.to_datetime(injuries['injury_date']).dt.year
        injuries['injury_month'] = pd.to_datetime(injuries['injury_date']).dt.month

        # Determine season (MLS season year)
        def get_season(year, month):
            # MLS season runs Feb-Oct
            # Jan-Jun injuries = current year's season
            # Jul-Dec injuries = current year's season
            # Exception: Nov-Jan = next year's season (offseason)
            if month in [11, 12, 1]:
                return str(year + 1) if month in [11, 12] else str(year)
            return str(year)

        injuries['season'] = injuries.apply(
            lambda row: get_season(row['injury_year'], row['injury_month']),
            axis=1
        )

        # Process each injury
        matched_count = 0

        for idx in tqdm(range(len(injuries)), desc="Matching injuries to fixtures"):
            row = injuries.iloc[idx]

            # Find the match where injury occurred
            match_info = self.find_match_for_injury(
                row['injury_date'],
                row['team'],
                row['season']
            )

            if match_info:
                # Update fixture info
                for key, value in match_info.items():
                    injuries.at[idx, key] = value

                # Now match to stadium based on HOME TEAM (not player's team!)
                home_team = match_info['home_team']
                injury_year = row['injury_year']

                # Find stadium where home team played
                stadium_match = stadiums[
                    (stadiums['team'] == home_team) &
                    (stadiums['start_year'] <= injury_year) &
                    (stadiums['end_year'] >= injury_year)
                ]

                if len(stadium_match) > 0:
                    stadium_info = stadium_match.iloc[0]
                    injuries.at[idx, 'stadium_name'] = stadium_info['stadium_name']
                    injuries.at[idx, 'surface_type'] = stadium_info['surface_type']
                    injuries.at[idx, 'city'] = stadium_info['city']
                    injuries.at[idx, 'state'] = stadium_info['state']
                    injuries.at[idx, 'altitude_ft'] = stadium_info['altitude_ft']
                    injuries.at[idx, 'climate_zone'] = stadium_info['climate_zone']
                    matched_count += 1

        # Save enhanced dataset
        injuries.to_csv(output_csv, index=False)
        logger.info(f"Saved fixture-matched data to {output_csv}")

        # Summary
        print("\n" + "="*70)
        print("FIXTURE MATCHING SUMMARY")
        print("="*70)
        print(f"Total injuries: {len(injuries):,}")
        print(f"Matched to fixtures: {matched_count:,} ({matched_count/len(injuries)*100:.1f}%)")
        print(f"Home games: {injuries['is_home_game'].sum():,}")
        print(f"Away games: {(~injuries['is_home_game']).sum():,}")
        print("\nTop stadiums by injury count:")
        print(injuries['stadium_name'].value_counts().head(10))
        print("="*70)

        return injuries


def main():
    """Main execution"""
    print("="*70)
    print("MLS Injury Data - Fixture-Based Stadium Matching")
    print("="*70)
    print("\nThis will:")
    print("  1. Cross-reference each injury date with team fixtures")
    print("  2. Determine if it was a home or away game")
    print("  3. Match to the HOME TEAM's stadium (actual location)")
    print("\nEstimated time: 8-12 hours (need to fetch fixtures for each injury)")
    print("="*70)

    matcher = FixtureMatchingService(delay=3.0)
    df = matcher.enhance_injuries_with_fixtures()


if __name__ == "__main__":
    main()
