#!/bin/bash

SCRIPT_DIR="$(dirname "$(readlink -f "$0")")"

python3 -c "
import sys
sys.path.insert(0, '$SCRIPT_DIR')
from startup_manager import run_at_startup
run_at_startup()
"