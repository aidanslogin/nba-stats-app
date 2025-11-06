#!/bin/bash
# Daily NBA data fetcher script
# This script is called by cron to update cached data

# Navigate to project directory
cd /Users/aidan/nba-stats-app

# Run the fetcher with Python 3
/usr/local/bin/python3 scripts/fetch_nba_data.py

# Log the timestamp
echo "NBA data fetch completed at $(date)" >> logs/fetch_log.txt
