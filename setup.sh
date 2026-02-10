#!/usr/bin/env bash
set -euo pipefail

./install_ubuntu_deps.sh

python3 -m venv .venv
source .venv/bin/activate

python -m pip install --upgrade pip
pip install -r requirements.txt

echo
echo "Done."
echo "Activate venv with: source .venv/bin/activate"
echo "Run with: python3 ds4_ur10_teleop.py"
