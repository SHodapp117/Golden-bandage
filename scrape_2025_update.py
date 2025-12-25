#!/usr/bin/env python3
"""
Update MLS injury data with latest 2025 season data
"""

from scrape_mls_injuries import TransfermarktScraper
import pandas as pd

def main():
    print("="*70)
    print("MLS Injury Data - 2025 Season Update")
    print("="*70)
    
    scraper = TransfermarktScraper(delay=3.0)
    
    # Only scrape 2024 and 2025 seasons for latest data
    seasons = ["2024", "2025"]
    
    print(f"\nUpdating data for seasons: {', '.join(seasons)}")
    print(f"This will add any new injuries since the last scrape")
    print(f"Rate limit: 3 seconds between requests\n")
    
    df_new = scraper.scrape_mls_injuries(
        seasons=seasons,
        output_file="mls_injuries_2025_update.csv"
    )
    
    if not df_new.empty:
        print("\n" + "="*70)
        print("UPDATE SUMMARY")
        print("="*70)
        print(f"✓ New injuries collected: {len(df_new)}")
        print(f"✓ Latest injury date: {df_new['injury_date'].max()}")
        
        # Merge with existing data
        print("\nMerging with existing data...")
        df_old = pd.read_csv("mls_player_injuries.csv")
        
        # Combine and remove duplicates
        df_combined = pd.concat([df_old, df_new])
        df_combined = df_combined.drop_duplicates(
            subset=['player_name', 'season', 'injury_date', 'injury_type', 'team']
        )
        
        # Save merged data
        df_combined.to_csv("mls_player_injuries.csv", index=False)
        
        new_records = len(df_combined) - len(df_old)
        
        print(f"\n✓ Previous total: {len(df_old):,} injuries")
        print(f"✓ New total: {len(df_combined):,} injuries")
        print(f"✓ Added: {new_records:,} new injuries")
        print(f"✓ Updated file: mls_player_injuries.csv")
        print("="*70)

if __name__ == "__main__":
    main()
