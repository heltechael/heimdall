#!/usr/bin/env bash
source $SOFTWAREPATH/SystemSoftware/services/conf/setup_prod.bash # Use prod env when training
DIR=$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )
TRAINING_SESSION_DIR=$(realpath "$DIR/..")
#/home/tbrain2/Software/SystemSoftware/Python/Annotator/models/YoloV5/Training/venv/bin/python "$DIR"/make_yolov5_datasets.py
"$TRAINING_SESSION_DIR/venv/bin/python" "$DIR/make_yolov5_datasets.py"
