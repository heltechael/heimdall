#!/usr/bin/env bash
source "$SOFTWAREPATH/SystemSoftware/services/conf/setup_prod.bash" # Use prod env when training
DIR=$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )
TRAINING_SESSION_DIR=$(realpath "$DIR/..")
# Config
export CUDA_DEVICE_ORDER="PCI_BUS_ID"  # use order from nvidia-smi
# --device 0 : The GTX GeForce 1080 TI
# --device 1 : The RTX A5000 card
# Check if the process is alrady running 
if [[ -f "$TRAINING_SESSION_DIR/pid" ]]; then
    pid=$(cat "$TRAINING_SESSION_DIR/pid")
tbrain2@roboweed-brain-dev:~/IGIS_software_michael/IGIS_software_michael/SystemSoftware/Python/Annotator/models/YoloV5/Training/utils$ cat publish_model.bash 
#!/usr/bin/env bash
source $SOFTWAREPATH/SystemSoftware/services/conf/setup_prod.bash # Use prod env when training
DIR=$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )
TRAINING_SESSION_DIR=$(realpath "$DIR/..")
SRC_DIR=$(realpath "$TRAINING_SESSION_DIR/src")
"$TRAINING_SESSION_DIR/venv/bin/python" "$SRC_DIR/publish_model.py" "$@"
tbrain2@roboweed-brain-dev:~/IGIS_software_michael/IGIS_software_michael/SystemSoftware/Python/Annotator/models/YoloV5/Training/utils$ ls
cd_results.bash     resume_training.bash  tensorboard_server.bash
publish_model.bash  stop_process.bash
tbrain2@roboweed-brain-dev:~/IGIS_software_michael/IGIS_software_michael/SystemSoftware/Python/Annotator/models/YoloV5/Training/utils$ cat resume_training.bash 
#!/usr/bin/env bash
source "$SOFTWAREPATH/SystemSoftware/services/conf/setup_prod.bash" # Use prod env when training
DIR=$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )
TRAINING_SESSION_DIR=$(realpath "$DIR/..")
# Config
export CUDA_DEVICE_ORDER="PCI_BUS_ID"  # use order from nvidia-smi
# --device 0 : The GTX GeForce 1080 TI
# --device 1 : The RTX A5000 card
# Check if the process is alrady running 
if [[ -f "$TRAINING_SESSION_DIR/pid" ]]; then
    pid=$(cat "$TRAINING_SESSION_DIR/pid")
    if [ -d "/proc/${pid}" ]; then
        echo "The process is aldready running ...";  # ToDo check if PID has been reused for anothe process
        exit 1
    fi
fi
# Check if there are any saved ephoc to continue from 
latest_folder=$(ls -1 "$SOFTWAREPATH/YoloV5RWM/runs/train/" | grep  "$project_name"  | sort -h | tail -n 1)
weights_path="$SOFTWAREPATH/YoloV5RWM/runs/train/$latest_folder/weights/last.pt"
if [ ! -f "$weights_path" ]; then
    echo "No saved epoch to continue from"
    exit 2
fi
# Change dir to avoid - relative path in YoloV5 to still match
cd "$SOFTWAREPATH/"SystemSoftware/Python/Annotator/models/YoloV5/Training || exit 3
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
nohup python "$SOFTWAREPATH/YoloV5RWM/train.py" --resume "$weights_path" --device 1 >> "$TRAINING_SESSION_DIR/out.txt" 2>&1 &
echo $! > "$TRAINING_SESSION_DIR/pid"
