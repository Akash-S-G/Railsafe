#!/usr/bin/env bash
# Hands-off runner: logs to runs/autonomous.log, resumes on crash
set -e
ROOT="$(cd "$(dirname "$0")/.." && pwd)"
mkdir -p "$ROOT/runs" "$ROOT/experiments/results"
echo "[$(date '+%H:%M:%S')] Starting autonomous CPU run (epochs 5) -> $ROOT/runs/autonomous.log"
nohup python "$ROOT/scripts/autonomous.py" --cpu --epochs 5 > "$ROOT/runs/autonomous.log" 2>&1 &
echo "PID $! — tail -f $ROOT/runs/autonomous.log"
echo "Checkpoints: cat $ROOT/experiments/results/autonomous_state.json"
echo "Report: cat $ROOT/experiments/results/autonomous_report.md"
