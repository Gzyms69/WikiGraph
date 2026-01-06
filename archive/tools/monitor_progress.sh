#!/bin/bash
# Monitor the number of processed batches
echo "Monitoring WikiGraph Progress..."
while true; do
    COUNT=$(ls -1 processed_batches_de/articles_batch_*.jsonl.gz 2>/dev/null | wc -l)
    ARTICLES=$((COUNT * 20000))
    SIZE=$(du -sh processed_batches_de/ | awk '{print $1}')
    echo "[$(date +%T)] Batches: $COUNT | Articles: ~$ARTICLES | Disk: $SIZE"
    sleep 10
done