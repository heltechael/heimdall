#!/usr/bin/env bash
source $SOFTWAREPATH/SystemSoftware/services/conf/setup_prod.bash # Use prod env when training
DIR=$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )
TRAINING_SESSION_PATH=$(realpath "$DIR"/..)
OUT_TRAIN_FILE=$TRAINING_SESSION_PATH/out.txt
echo "Training session: $TRAINING_SESSION_PATH" >> "$OUT_TRAIN_FILE"
touch "$OUT_TRAIN_FILE"
# Prepare data set
echo "Make CSV datasets" >> "$OUT_TRAIN_FILE"
if ! "$TRAINING_SESSION_PATH/src/make_yolov5_datasets.bash" >> "$OUT_TRAIN_FILE" 2>&1;
then
    exit 1;
fi
# Make sym link
project_name="igis_$(basename "$TRAINING_SESSION_PATH")"
latest_folder=$(ls -1 "$SOFTWAREPATH/YoloV5RWM/runs/train" | grep  "$project_name"  | sort -h | tail -n 1)
result_dir_all="$SOFTWAREPATH/YoloV5RWM/runs/train"  # show all
result_dir="$result_dir_all/$latest_folder"  # show only current
ln -s "$result_dir" "$TRAINING_SESSION_PATH"/results
# Start the training procedure
echo "Start trainig" >> "$OUT_TRAIN_FILE"
if ! "$TRAINING_SESSION_PATH/src/train_yolov5_network.bash" >> "$OUT_TRAIN_FILE" 2>&1;
then
    exit 2;
fi
