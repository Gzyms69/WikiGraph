#!/bin/bash
set -e

# Configuration
export PYTHONPATH=.
export WIKIGRAPH_HEAP=14G

echo "🚀 Starting Manual Spanish Triangle Count (Pruned)..."
echo "1. Ensuring Spanish Container is running (Restarting to apply 14GB Heap)..."
python3 tools/ops/manage_containers.py stop es
python3 tools/ops/manage_containers.py start es

echo "2. Running Computation (Estimated 30-40 minutes)..."
echo "   Note: Heartbeats will print every 30 seconds."
python3 tools/analytics/compute_global_metrics.py --lang es --algorithms triangleCount

echo "✅ Done."
echo "To stop the container and free RAM, run: ./dev.sh stop es"
