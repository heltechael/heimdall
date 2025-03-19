#!/usr/bin/env bash
source "$SOFTWAREPATH/SystemSoftware/services/conf/setup_prod.bash" # Use prod env when training
DIR=$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )
TRAINING_SESSION_DIR=$(realpath "$DIR/..")
# Config
export CUDA_DEVICE_ORDER="PCI_BUS_ID"  # use order from nvidia-smi
# --device 0 : The GTX GeForce 1080 TI
# --device 1 : The RTX A5000 card
# Set up env (conda)
source /home/tbrain2/anaconda3/etc/profile.d/conda.sh
conda activate YoloV5_Python3.8_Cuda11.7 # Swift to the conda enviroment with cuda and pytorch setup
echo "Use conda env: $CONDA_DEFAULT_ENV"  # Check activated conda env
# Print python path
which python
# Set nices level
renice -n 19 $$
# Start Training
project_name="igis_$(basename "$TRAINING_SESSION_DIR")"
python "$SOFTWAREPATH/YoloV5RWM/train.py" \
    --data "$TRAINING_SESSION_DIR/data/dataset.yaml" \
    --weights pre_t/yolov5l.pt \
    --batch-size 7 \
    --img-size 1600 \
    --name "$project_name" \
    --device 1 >> "$TRAINING_SESSION_DIR/out.txt"
