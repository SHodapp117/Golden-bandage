#!/bin/bash
# Monitor the MLS injury scraper progress

echo "======================================================================="
echo "MLS Injury Scraper Monitor"
echo "======================================================================="
echo ""

# Check if scraper is running
if ps aux | grep -v grep | grep scrape_mls_injuries.py > /dev/null; then
    echo "✓ Scraper is RUNNING"
    echo ""
    echo "Process info:"
    ps aux | grep -v grep | grep scrape_mls_injuries.py | awk '{print "  PID: " $2 "  CPU: " $3"%  MEM: " $4"%  TIME: " $10}'
else
    echo "✗ Scraper is NOT running"
fi

echo ""
echo "-----------------------------------------------------------------------"
echo "Latest log output:"
echo "-----------------------------------------------------------------------"
tail -30 scraper_output.log

echo ""
echo "-----------------------------------------------------------------------"
echo "Data collection progress:"
echo "-----------------------------------------------------------------------"

# Check if output file exists
if [ -f "mls_player_injuries.csv" ]; then
    RECORDS=$(wc -l < mls_player_injuries.csv)
    echo "  Records collected: $RECORDS"
    echo "  File size: $(du -h mls_player_injuries.csv | awk '{print $1}')"
else
    echo "  No data file yet (mls_player_injuries.csv)"
fi

echo ""
echo "-----------------------------------------------------------------------"
echo "Commands:"
echo "  Watch live: tail -f scraper_output.log"
echo "  Stop scraper: pkill -f scrape_mls_injuries.py"
echo "  Re-run monitor: bash monitor_scraper.sh"
echo "======================================================================="
