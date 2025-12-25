#!/bin/bash
echo "======================================================================="
echo "2025 Season Update Monitor"
echo "======================================================================="
echo ""

# Check if scraper is running
if ps aux | grep -v grep | grep scrape_2025_update.py > /dev/null; then
    echo "✓ Update scraper is RUNNING"
    echo ""
    ps aux | grep -v grep | grep scrape_2025_update.py | awk '{print "  PID: " $2 "  CPU: " $3"%  MEM: " $4"%"}'
else
    echo "✗ Update scraper is NOT running"
fi

echo ""
echo "-----------------------------------------------------------------------"
echo "Latest log output:"
echo "-----------------------------------------------------------------------"
tail -20 scraper_2025_update.log

echo ""
echo "-----------------------------------------------------------------------"
if [ -f "mls_injuries_2025_update.csv" ]; then
    RECORDS=$(wc -l < mls_injuries_2025_update.csv)
    echo "New records collected: $RECORDS"
else
    echo "No update file yet"
fi

echo "-----------------------------------------------------------------------"
echo "Commands: tail -f scraper_2025_update.log"
echo "======================================================================="
