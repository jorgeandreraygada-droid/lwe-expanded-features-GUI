#!/bin/bash

# Get the directory where this script is located (source/core/)
SCRIPT_DIR="$(dirname "$(readlink -f "$0")")"

# Change to the script directory so main.sh can find its dependencies
cd "$SCRIPT_DIR" || exit 1

# Call the Python startup function
python3 -c "
import sys
sys.path.insert(0, '$SCRIPT_DIR')
from startup_manager import run_at_startup
run_at_startup()
"