#!/bin/bash
# Simple Resource Monitor
echo "Monitoring Resources (Ctrl+C to stop)..."
printf "% -10s % -10s % -10s % -10s\n" "CPU%" "MEM_MB" "FREE_GB" "SWAP_MB"
while true; do
    CPU=$(top -bn1 | grep "Cpu(s)" | awk '{print $2 + $4}')
    MEM=$(ps -u $USER -o rss | awk '{sum+=$1} END {print sum/1024}')
    FREE=$(free -g | grep "Mem:" | awk '{print $4}')
    SWAP=$(free -m | grep "Swap:" | awk '{print $3}')
    printf "% -10s % -10.0f % -10s % -10s\n" "$CPU" "$MEM" "$FREE" "$SWAP"
    sleep 2
done