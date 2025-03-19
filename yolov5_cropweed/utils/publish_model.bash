#!/usr/bin/env bash
source $SOFTWAREPATH/SystemSoftware/services/conf/setup_prod.bash # Use prod env when training
DIR=$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )
TRAINING_SESSION_DIR=$(realpath "$DIR/..")
SRC_DIR=$(realpath "$TRAINING_SESSION_DIR/src")
"$TRAINING_SESSION_DIR/venv/bin/python" "$SRC_DIR/publish_model.py" "$@"
