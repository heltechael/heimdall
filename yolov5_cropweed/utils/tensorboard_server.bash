#!/usr/bin/env bash
source "$SOFTWAREPATH/SystemSoftware/services/conf/setup_prod.bash" # Use prod env when training
DIR=$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )
TRAINING_SESSION_DIR=$(realpath "$DIR/..")
# Set up env (conda)
source /home/tbrain2/anaconda3/etc/profile.d/conda.sh
conda activate YoloV5_Python3.8_Cuda11.7 # Swift to the conda enviroment with cuda and pytorch setup
echo "Use conda env: $CONDA_DEFAULT_ENV"  # Check activated conda env
project_name="igis_$(basename "$TRAINING_SESSION_DIR")"
if [ -z "$(ls -A "$SOFTWAREPATH/YoloV5RWM/runs/train")" ]; then
   echo "No runs folder was found!"
   echo "Note: If you have started a new training session, it has probably just not been created yet."
   exit
fi
latest_folder=$(ls -1 "$SOFTWAREPATH/YoloV5RWM/runs/train" | grep  "$project_name"  | sort -h | tail -n 1)
log_dir_all="$SOFTWAREPATH/YoloV5RWM/runs/train"  # show all
log_dir="$log_dir_all/$latest_folder"  # show only current
echo "$log_dir"
tensorboard --host "$(ip route get 1 | head -n1  | awk '{print $7}')" --logdir "$log_dir_all"
