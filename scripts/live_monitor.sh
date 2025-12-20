#!/bin/bash
# ~/WikiGraph/scripts/live_monitor.sh

echo "=== LIVE PROCESSING MONITOR ==="
echo "Updated every 30 seconds"
echo "Press Ctrl+C to exit"
echo ""

while true; do
    clear

    # Get current timestamp
    echo "Time: $(date '+%Y-%m-%d %H:%M:%S')"
    echo "=========================================="

    # Count batch files
    if ls /mnt/c/Users/PC/WikiGraph/processed_batches/articles_batch_*.jsonl.gz 1> /dev/null 2>&1; then
        BATCH_COUNT=$(ls -1 /mnt/c/Users/PC/WikiGraph/processed_batches/articles_batch_*.jsonl.gz | wc -l)
        ARTICLE_COUNT=$((BATCH_COUNT * 2000))

        # Get last batch number
        LAST_BATCH=$(ls -1 /mnt/c/Users/PC/WikiGraph/processed_batches/articles_batch_*.jsonl.gz | tail -1 | grep -o '[0-9][0-9][0-9][0-9]' | tail -1)
        LAST_BATCH=${LAST_BATCH:-0}

        # Estimate progress (2M total)
        if [ "$LAST_BATCH" -gt 0 ]; then
            PERCENT=$(echo "scale=2; $ARTICLE_COUNT / 2000000 * 100" | bc)
        else
            PERCENT=0
        fi

        # Count total links (approximate)
        LINK_COUNT=0
        for file in /mnt/c/Users/PC/WikiGraph/processed_batches/links_batch_*.csv.gz; do
            if [ -f "$file" ]; then
                COUNT=$(zcat "$file" 2>/dev/null | wc -l 2>/dev/null || echo "0")
                LINK_COUNT=$((LINK_COUNT + COUNT))
            fi
        done

        # Memory usage of parser process
        PIDS=$(pgrep -f "phase1_production.py")
        if [ -n "$PIDS" ]; then
            MEMORY_MB=$(ps -p $PIDS -o rss= | awk '{printf "%.1f", $1/1024}')
        else
            MEMORY_MB="0.0"
        fi

        # Check log for latest activity
        LATEST_LOG=$(tail -5 /mnt/c/Users/PC/WikiGraph/processed_batches/parser.log 2>/dev/null | grep -E "Processed|SUCCESS" | tail -1)

        echo "Batches completed: $BATCH_COUNT"
        echo "Articles processed: $ARTICLE_COUNT"
        echo "Estimated progress: $PERCENT%"
        echo "Links extracted: $LINK_COUNT"
        echo "Memory usage: ${MEMORY_MB}MB"
        echo "Last batch: $LAST_BATCH"
        echo ""

        if [ -n "$LATEST_LOG" ]; then
            echo "Recent activity:"
            echo "$LATEST_LOG"
        fi

        # Show sample from latest batch
        if [ $BATCH_COUNT -gt 0 ]; then
            echo ""
            echo "Latest batch sample (5 articles):"
            LATEST_FILE=$(ls -1 /mnt/c/Users/PC/WikiGraph/processed_batches/articles_batch_*.jsonl.gz | tail -1)
            zcat "$LATEST_FILE" 2>/dev/null | tail -5 | jq -r '.title' 2>/dev/null || echo "  (Could not read file)"
        fi

    else
        echo "No batch files found yet..."
        echo "Processing may be starting or in early stages."
    fi

    echo ""
    echo "------------------------------------------"
    echo "Next update in 30 seconds..."
    sleep 30
done
