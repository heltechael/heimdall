#!/usr/bin/env bash
source $SOFTWAREPATH/SystemSoftware/services/conf/setup_prod.bash # Use prod env when training
DIR=$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )
TRAINING_PATH=$TRAINING_SESSIONS_PATH_ANNOTATOR # env variable
TRAINING_SESSION_PATH=$TRAINING_PATH/$(date +%F_%H-%M-%S)
echo "Start training session: $TRAINING_SESSION_PATH"
# Make train session folder
mkdir -p $TRAINING_SESSION_PATH
# Copy software to session folder
echo "Copy src folder..."
cp -r "$DIR/src" "$TRAINING_SESSION_PATH"
# Check copy of src
MD5_SRC=$(find "$DIR/src" -type f -exec md5sum {} \; |  awk '{ print $1 }' | sort | md5sum)
MD5_TRAINING_SESSION_PATH=$(find "$TRAINING_SESSION_PATH/src" -type f -exec md5sum {} \; | awk '{ print $1 }' | sort | md5sum)
if [ "$MD5_SRC" != "$MD5_TRAINING_SESSION_PATH" ]; then
	echo "Invalid MD5 sum for src folder: $MD5_TRAINING_SESSION_PATH should be $MD5_SRC!"
	exit 1
fi
echo "Copy utils folder..."
cp -r "$DIR/utils" "$TRAINING_SESSION_PATH"
tbrain2@roboweed-brain-dev:~/IGIS_software_michael/IGIS_software_michael/SystemSoftware/Python/Annotator/models/YoloV5/Training$ cat train_annotator.bash 
#!/usr/bin/env bash
source $SOFTWAREPATH/SystemSoftware/services/conf/setup_prod.bash # Use prod env when training
DIR=$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )
TRAINING_PATH=$TRAINING_SESSIONS_PATH_ANNOTATOR # env variable
TRAINING_SESSION_PATH=$TRAINING_PATH/$(date +%F_%H-%M-%S)
echo "Start training session: $TRAINING_SESSION_PATH"
# Make train session folder
mkdir -p $TRAINING_SESSION_PATH
# Copy software to session folder
echo "Copy src folder..."
cp -r "$DIR/src" "$TRAINING_SESSION_PATH"
# Check copy of src
MD5_SRC=$(find "$DIR/src" -type f -exec md5sum {} \; |  awk '{ print $1 }' | sort | md5sum)
MD5_TRAINING_SESSION_PATH=$(find "$TRAINING_SESSION_PATH/src" -type f -exec md5sum {} \; | awk '{ print $1 }' | sort | md5sum)
if [ "$MD5_SRC" != "$MD5_TRAINING_SESSION_PATH" ]; then
	echo "Invalid MD5 sum for src folder: $MD5_TRAINING_SESSION_PATH should be $MD5_SRC!"
	exit 1
fi
echo "Copy utils folder..."
cp -r "$DIR/utils" "$TRAINING_SESSION_PATH"
# Check copy of utils
MD5_SRC=$(find "$DIR/utils" -type f -exec md5sum {} \; |  awk '{ print $1 }' | sort | md5sum)
MD5_TRAINING_SESSION_PATH=$(find "$TRAINING_SESSION_PATH/utils" -type f -exec md5sum {} \; | awk '{ print $1 }' | sort | md5sum)
if [ "$MD5_SRC" != "$MD5_TRAINING_SESSION_PATH" ]; then
	echo "Invalid MD5 sum for utils folder: $MD5_TRAINING_SESSION_PATH should be $MD5_SRC!"
	exit 1
fi
echo "Copy venv folder..."
cp -rL "$DIR/venv" "$TRAINING_SESSION_PATH" # ToDo: pip freeze > requirements_tmp.txt && pip install -r requirements_tmp.txt
# Start the trainning procedure
echo "Start ..."
nohup "$TRAINING_SESSION_PATH/src/main.bash" &
echo $! > "$TRAINING_SESSION_PATH/pid"
