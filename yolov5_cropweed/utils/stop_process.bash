#!/usr/bin/env bash
source "$SOFTWAREPATH/SystemSoftware/services/conf/setup_prod.bash" # Use prod env when training
DIR=$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )
TRAINING_SESSION_DIR=$(realpath "$DIR/..")
source "$SOFTWAREPATH/SystemSoftware/Bash/src/confirm.bash"
if [[ ! -f "$TRAINING_SESSION_DIR/pid" ]]; then
    echo "pid was not found!"
    exit 1
fi
pid=$(cat "$TRAINING_SESSION_DIR/pid")
if [ ! -d "/proc/${pid}" ]; then
    echo "The process $pid is not running...";
    exit 2
fi
confirm_yes "Would you really like to stop the trainning session (yes|no)?" && kill $(ps -o pid= -s $(ps -o sess --no-heading --pid "$pid"))
