#!/bin/bash
# Monitor the MLS injury data collection progress

echo "======================================"
echo "MLS Injury Data Collection Progress"
echo "======================================"
echo ""

# Check if scraper is still running
if ps -p 56797 > /dev/null 2>&1; then
    echo "✓ Scraper is RUNNING (PID: 56797)"
else
    echo "✗ Scraper has STOPPED"
fi

echo ""
echo "Recent log output:"
echo "--------------------------------------"
tail -20 scraper_output.log

echo ""
echo "--------------------------------------"

# Check if output file exists and show stats
if [ -f "mls_player_injuries.csv" ]; then
    record_count=$(wc -l < mls_player_injuries.csv)
    record_count=$((record_count - 1))  # Subtract header
    echo "Injuries collected so far: $record_count"

    file_size=$(ls -lh mls_player_injuries.csv | awk '{print $5}')
    echo "File size: $file_size"
else
    echo "Output file not yet created"
fi

echo ""
echo "To check progress again, run: bash check_progress.sh"
echo "To view full log: tail -f scraper_output.log"
echo "======================================"
