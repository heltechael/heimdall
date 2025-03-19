#!/usr/bin/env bash
# Change directory to the folder with weights
source "$SOFTWAREPATH/SystemSoftware/services/conf/setup_prod.bash" # Use prod env when training
DIR=$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )
TRAINING_SESSION_DIR=$(realpath "$DIR/..")
project_name="igis_$(basename "$TRAINING_SESSION_DIR")"
latest_folder=$(ls -1 "$SOFTWAREPATH/YoloV5RWM/runs/train" | grep  "$project_name"  | sort -h | tail -n 1)
result_dir_all="$SOFTWAREPATH/YoloV5RWM/runs/train"  # show all
result_dir="$result_dir_all/$latest_folder"  # show only current
echo cd "$result_dir" || exit
