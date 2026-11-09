#!/usr/bin/env bash
# Барлық эксперименттерді бірдей шартта ретімен орындау
set -e
cd "$(dirname "$0")/.."
for c in configs/E0*.json; do
  python -m src.train --config "$c"
done
python -m src.evaluate --select-best
