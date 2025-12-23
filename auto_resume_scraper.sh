#!/bin/bash
# Auto-resume scraper script
# Checks every 45 seconds and restarts if stopped

LOG_FILE="scraper_output.log"
SCRIPT_NAME="scrape_mls_injuries.py"
CHECK_INTERVAL=45  # 45 seconds

echo "Starting auto-resume monitor for MLS scraper..."
echo "Check interval: 45 seconds"
echo "Log file: $LOG_FILE"
echo ""

# Start the scraper initially
if ! pgrep -f "python3 $SCRIPT_NAME" > /dev/null; then
    echo "[$(date '+%Y-%m-%d %H:%M:%S')] Starting scraper..."
    python3 "$SCRIPT_NAME" > "$LOG_FILE" 2>&1 &
    echo "Scraper started (PID: $!)"
else
    echo "[$(date '+%Y-%m-%d %H:%M:%S')] Scraper already running"
fi

# Monitor loop
while true; do
    sleep $CHECK_INTERVAL

    # Check if scraper is running
    if pgrep -f "python3 $SCRIPT_NAME" > /dev/null; then
        echo "[$(date '+%Y-%m-%d %H:%M:%S')] ✓ Scraper is running"

        # Show progress
        if [ -f scraper_checkpoint.json ]; then
            PLAYERS=$(python3 -c "import json; data=json.load(open('scraper_checkpoint.json')); print(len(data['processed_players']))" 2>/dev/null || echo "?")
            RECORDS=$(wc -l < mls_player_injuries.csv 2>/dev/null || echo "?")
            echo "  Progress: $PLAYERS players processed, $RECORDS injury records"
        fi
    else
        echo "[$(date '+%Y-%m-%d %H:%M:%S')] ✗ Scraper stopped - restarting..."
        python3 "$SCRIPT_NAME" >> "$LOG_FILE" 2>&1 &
        NEW_PID=$!
        echo "  Restarted (PID: $NEW_PID)"

        # Give it a moment to start
        sleep 5

        if pgrep -f "python3 $SCRIPT_NAME" > /dev/null; then
            echo "  ✓ Restart successful"
        else
            echo "  ✗ Restart failed - will retry in 45 seconds"
        fi
    fi
done
