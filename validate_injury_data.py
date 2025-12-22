#!/usr/bin/env python3
"""
Data Validation and Analysis Script
Validates collected MLS injury data against medical research benchmarks
"""

import pandas as pd
import numpy as np
from typing import Dict, List, Tuple
import logging

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class InjuryDataValidator:
    """Validates injury data against medical research benchmarks"""

    def __init__(
        self,
        injury_data_path: str = "mls_player_injuries_enhanced.csv",
        benchmark_path: str = "injury_recovery_timelines.csv"
    ):
        """
        Initialize validator with data paths

        Args:
            injury_data_path: Path to collected injury data
            benchmark_path: Path to medical benchmark data
        """
        self.injury_data = pd.read_csv(injury_data_path)
        self.benchmarks = pd.read_csv(benchmark_path)

    def validate_data_quality(self) -> Dict:
        """
        Check data quality and completeness

        Returns:
            Dictionary with quality metrics
        """
        logger.info("Validating data quality...")

        total_records = len(self.injury_data)

        quality_metrics = {
            'total_records': total_records,
            'complete_records': 0,
            'missing_injury_type': 0,
            'missing_dates': 0,
            'missing_duration': 0,
            'missing_performance': 0,
            'duplicate_records': 0,
            'data_quality_score': 0.0
        }

        # Check for missing critical fields
        quality_metrics['missing_injury_type'] = self.injury_data['injury_type'].isna().sum()
        quality_metrics['missing_dates'] = (
            self.injury_data['injury_date'].isna().sum() +
            self.injury_data['return_date'].isna().sum()
        )
        quality_metrics['missing_duration'] = self.injury_data['days_out'].isna().sum()
        quality_metrics['missing_performance'] = (
            self.injury_data['performance_before_injury'].isna().sum()
        )

        # Check for duplicates
        quality_metrics['duplicate_records'] = self.injury_data.duplicated(
            subset=['player_name', 'injury_date', 'injury_type']
        ).sum()

        # Calculate complete records
        quality_metrics['complete_records'] = total_records - max(
            quality_metrics['missing_injury_type'],
            quality_metrics['missing_dates'],
            quality_metrics['missing_duration']
        )

        # Calculate quality score (0-100)
        completeness = quality_metrics['complete_records'] / total_records if total_records > 0 else 0
        quality_metrics['data_quality_score'] = round(completeness * 100, 2)

        return quality_metrics

    def compare_recovery_times(self) -> pd.DataFrame:
        """
        Compare collected recovery times with medical benchmarks

        Returns:
            DataFrame with comparison results
        """
        logger.info("Comparing recovery times with benchmarks...")

        # Map injury types to benchmark categories
        injury_mapping = {
            'hamstring': 'Hamstring Strain',
            'adductor': 'Adductor Strain',
            'groin': 'Adductor Strain',
            'acl': 'ACL',
            'anterior cruciate': 'ACL',
            'ankle': 'Ankle Sprain',
            'mcl': 'MCL',
            'medial collateral': 'MCL'
        }

        comparisons = []

        for injury_key, benchmark_type in injury_mapping.items():
            # Filter collected data
            collected = self.injury_data[
                self.injury_data['injury_type'].str.lower().str.contains(injury_key, na=False)
            ]

            if len(collected) == 0:
                continue

            # Get benchmark data
            benchmark = self.benchmarks[
                self.benchmarks['injury_type'] == benchmark_type
            ]

            if len(benchmark) == 0:
                continue

            # Calculate statistics
            collected_mean = collected['days_out'].mean()
            collected_median = collected['days_out'].median()
            collected_std = collected['days_out'].std()
            collected_count = len(collected)

            # Get most recent benchmark (prefer 2016-2021 data)
            recent_benchmark = benchmark[
                benchmark['time_period'].str.contains('2016-2021', na=False)
            ]
            if len(recent_benchmark) == 0:
                recent_benchmark = benchmark

            benchmark_median = recent_benchmark['median_recovery_days'].mean()
            benchmark_mean = recent_benchmark['mean_recovery_days'].mean()

            # Calculate difference
            median_diff = collected_median - benchmark_median
            median_diff_pct = (median_diff / benchmark_median * 100) if benchmark_median > 0 else 0

            comparisons.append({
                'injury_type': benchmark_type,
                'collected_count': collected_count,
                'collected_median_days': round(collected_median, 1),
                'collected_mean_days': round(collected_mean, 1),
                'collected_std_days': round(collected_std, 1),
                'benchmark_median_days': round(benchmark_median, 1),
                'benchmark_mean_days': round(benchmark_mean, 1),
                'difference_days': round(median_diff, 1),
                'difference_percent': round(median_diff_pct, 1),
                'within_expected_range': abs(median_diff_pct) < 20  # Within 20%
            })

        return pd.DataFrame(comparisons)

    def analyze_position_patterns(self) -> pd.DataFrame:
        """
        Analyze injury patterns by player position

        Returns:
            DataFrame with position-based analysis
        """
        logger.info("Analyzing injury patterns by position...")

        position_analysis = self.injury_data.groupby('position').agg({
            'player_name': 'count',
            'days_out': ['mean', 'median', 'std'],
            'games_missed': ['mean', 'median']
        }).round(1)

        position_analysis.columns = [
            'total_injuries',
            'avg_days_out',
            'median_days_out',
            'std_days_out',
            'avg_games_missed',
            'median_games_missed'
        ]

        return position_analysis.sort_values('total_injuries', ascending=False)

    def analyze_seasonal_trends(self) -> pd.DataFrame:
        """
        Analyze injury trends over seasons

        Returns:
            DataFrame with seasonal trends
        """
        logger.info("Analyzing seasonal trends...")

        seasonal = self.injury_data.groupby('season').agg({
            'player_name': 'count',
            'days_out': 'median',
            'games_missed': 'median'
        }).round(1)

        seasonal.columns = ['total_injuries', 'median_days_out', 'median_games_missed']

        return seasonal.sort_index()

    def analyze_performance_impact(self) -> Dict:
        """
        Analyze impact of injuries on player performance

        Returns:
            Dictionary with performance impact metrics
        """
        logger.info("Analyzing performance impact...")

        # Filter records with both pre and post performance data
        complete_perf = self.injury_data[
            (self.injury_data['performance_before_injury'].notna()) &
            (self.injury_data['performance_after_injury'].notna())
        ]

        if len(complete_perf) == 0:
            return {
                'records_with_performance_data': 0,
                'avg_performance_decline': None,
                'players_with_decline': None,
                'players_with_improvement': None
            }

        # Calculate performance change
        complete_perf['performance_change'] = (
            complete_perf['performance_after_injury'] -
            complete_perf['performance_before_injury']
        )

        complete_perf['performance_change_pct'] = (
            complete_perf['performance_change'] /
            complete_perf['performance_before_injury'] * 100
        )

        return {
            'records_with_performance_data': len(complete_perf),
            'avg_performance_before': round(complete_perf['performance_before_injury'].mean(), 3),
            'avg_performance_after': round(complete_perf['performance_after_injury'].mean(), 3),
            'avg_performance_change': round(complete_perf['performance_change'].mean(), 3),
            'avg_performance_change_pct': round(complete_perf['performance_change_pct'].mean(), 1),
            'players_with_decline': (complete_perf['performance_change'] < 0).sum(),
            'players_with_improvement': (complete_perf['performance_change'] > 0).sum(),
            'players_unchanged': (complete_perf['performance_change'] == 0).sum()
        }

    def generate_report(self, output_file: str = "validation_report.txt"):
        """
        Generate comprehensive validation report

        Args:
            output_file: Path to output report file
        """
        logger.info("Generating validation report...")

        with open(output_file, 'w') as f:
            f.write("="*80 + "\n")
            f.write("MLS INJURY DATA VALIDATION REPORT\n")
            f.write("="*80 + "\n\n")

            # Data Quality
            f.write("1. DATA QUALITY METRICS\n")
            f.write("-"*80 + "\n")
            quality = self.validate_data_quality()
            for key, value in quality.items():
                f.write(f"  {key.replace('_', ' ').title()}: {value}\n")
            f.write("\n")

            # Recovery Time Comparison
            f.write("2. RECOVERY TIME COMPARISON (Collected vs Research Benchmarks)\n")
            f.write("-"*80 + "\n")
            comparison = self.compare_recovery_times()
            f.write(comparison.to_string(index=False))
            f.write("\n\n")

            # Position Analysis
            f.write("3. INJURY PATTERNS BY POSITION\n")
            f.write("-"*80 + "\n")
            position = self.analyze_position_patterns()
            f.write(position.to_string())
            f.write("\n\n")

            # Seasonal Trends
            f.write("4. SEASONAL TRENDS\n")
            f.write("-"*80 + "\n")
            seasonal = self.analyze_seasonal_trends()
            f.write(seasonal.to_string())
            f.write("\n\n")

            # Performance Impact
            f.write("5. PERFORMANCE IMPACT ANALYSIS\n")
            f.write("-"*80 + "\n")
            performance = self.analyze_performance_impact()
            for key, value in performance.items():
                f.write(f"  {key.replace('_', ' ').title()}: {value}\n")
            f.write("\n")

            f.write("="*80 + "\n")
            f.write("End of Report\n")
            f.write("="*80 + "\n")

        logger.info(f"Report saved to {output_file}")

        # Also print summary to console
        print("\n" + "="*80)
        print("VALIDATION SUMMARY")
        print("="*80)
        print(f"\nData Quality Score: {quality['data_quality_score']}%")
        print(f"Total Records: {quality['total_records']}")
        print(f"Complete Records: {quality['complete_records']}")
        print("\nRecovery Time Validation:")
        print(comparison[['injury_type', 'collected_median_days', 'benchmark_median_days', 'within_expected_range']].to_string(index=False))
        print("\n" + "="*80)


def main():
    """Main execution"""
    try:
        validator = InjuryDataValidator(
            injury_data_path="mls_player_injuries_enhanced.csv",
            benchmark_path="injury_recovery_timelines.csv"
        )

        validator.generate_report("validation_report.txt")

        logger.info("Validation complete!")

    except FileNotFoundError as e:
        logger.error(f"Data file not found: {e}")
        logger.error("Please run scrape_mls_injuries.py first to collect data")
    except Exception as e:
        logger.error(f"Validation failed: {e}")


if __name__ == "__main__":
    main()
