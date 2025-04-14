#!/bin/bash

PROCESS_NAME="bitz"
LOG_FILE="cpu_usage_${PROCESS_NAME}.log"
INTERVAL=1 # seconds

echo "Monitoring CPU usage for process '$PROCESS_NAME' every $INTERVAL second(s)..."
echo "Logging to $LOG_FILE"

# Write header only if file doesn't exist or is empty
if [ ! -f "$LOG_FILE" ] || [ ! -s "$LOG_FILE" ]; then
    echo "Timestamp, CPU%" > "$LOG_FILE"
fi

# Find the PID - handle multiple processes if necessary, here we take the first one
PID=$(pgrep -f "$PROCESS_NAME" | head -n 1)

if [ -z "$PID" ]; then
    echo "Error: Process '$PROCESS_NAME' not found."
    exit 1
fi

echo "Found $PROCESS_NAME process with PID: $PID"

# Loop to monitor CPU usage
while ps -p "$PID" > /dev/null; do # Check if process still exists
    # Get CPU usage for the specific PID
    # The 'ps -p $PID -o %cpu' command outputs the CPU usage percentage
    CPU_USAGE=$(ps -p "$PID" -o %cpu | tail -n 1 | awk '{print $1}')

    # Get current timestamp
    TIMESTAMP=$(date +"%Y-%m-%d %H:%M:%S")

    # Log timestamp and CPU usage (only append to file)
    echo "$TIMESTAMP, $CPU_USAGE" >> "$LOG_FILE" # Changed this line

    # Wait for the next interval
    sleep "$INTERVAL"
done

echo "Process $PID ($PROCESS_NAME) seems to have terminated."
echo "CPU usage log saved to $LOG_FILE"