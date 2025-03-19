#!/usr/bin/env python3
import argparse
import glob
import json
import os
import sys
from typing import Any, Dict, List, Literal, Optional
from datetime import datetime
import yaml
# Misc
from AgroDB import RoboWeedMaPSDB
from Misc.path import mkdir_p, copy_smart
DIR = os.path.abspath(os.path.join(__file__, os.pardir))
TRAINING_SESSION_DIR = os.path.abspath(os.path.join(DIR, os.pardir))
DATA_DIR = os.path.abspath(os.path.join(TRAINING_SESSION_DIR, 'data'))
RELEASED_MODEL_DIR = '/mnt/models/Annotation'
TEST_DATABASE_NAME = 'RoboWeedMapsTest'
PROD_DATABASE_NAME = 'RoboWeedMaps'
DATA_CONFIG_YAML_FILENAME = 'dataset.yaml' # data-configurations yaml file (used by YoloV5 train.py)
MODEL_TYPE = 'Annotation'
DATA_CONFIG_YAML_PATH = os.path.join(DATA_DIR, DATA_CONFIG_YAML_FILENAME)
def parse_args(args):
    parser = argparse.ArgumentParser(description='Script for publish a crop-weed detection (the "annotation") model to the RWM system')
    parser.add_argument('-v', '---version', metavar='v', type=int, help='The crop-weed detection model release version number e.g 42', required=True)
    parser.add_argument('-t', '--publish-to-test', help='Publish the model to TEST', dest='publish_to_test', action='store_true', default=False)
    parser.add_argument('-p', '--publish-to-prod', help='Publish the model to PRODUCTION', dest='publish_to_prod', action='store_true', default=False)
    return parser.parse_args(args)
def get_training_session_datetime() -> datetime:
    name = os.path.basename(TRAINING_SESSION_DIR)
    return datetime.strptime(name,'%Y-%m-%d_%H-%M-%S')
def get_training_session_name() -> str:
    session_datetime = get_training_session_datetime()
    session_string = session_datetime.strftime('%Y-%m-%d_%H-%M-%S')
    try:
        if not session_string == os.path.basename(TRAINING_SESSION_DIR):
            raise ValueError
    except ValueError:
        raise 'You must publish a model from a training session folder'
    return session_string
def load_eppo_codes() -> List[str]:
    with open(DATA_CONFIG_YAML_PATH, 'r') as fp:
        data_config = yaml.safe_load(fp)
        return data_config['names']
def make_model_json(
        model_dir: str,
        version: Optional[int]) -> str:
    info = {
        "Project": "RWM", 
        "EppoCode": load_eppo_codes(), 
        "ModelVersion": ("V%d" % version) if version else None, 
        "Date": str(get_training_session_datetime().strftime('%d%b_%y')), 
        "License": "NA"
    }
    json_path =  os.path.join(model_dir, 'Model_json.json')
    print("make %s" % json_path)
    if not os.path.exists(json_path):
        with open(json_path, "w") as fp:
            json.dump(info, fp)
            fp.write(os.linesep)
    return json_path
def copy_weights(session_name: str, model_dir:str) -> str:
    # Find project folder (YoloV5 make a new folder for project when a train.py is started)
    project_name=session_name  # We use session name as project name
    train_dir = os.path.join(os.environ["SOFTWAREPATH"],"YoloV5RWM","runs","train")
    project_dir = os.path.join(train_dir, 'igis_'+project_name)
    # Yolov5 train.py will make a new folder for each time a project is trainned
    # We'll take the latest (normaly use there should only be one) 
    project_folder_runs = glob.glob(project_dir+'*')
    latest_project_folder = sorted(project_folder_runs)[0]  # e.g. /home/tbrain2/Software/YoloV5RWM/runs/train/igis_2022-11-03_13-38-41
    best_weightfile = os.path.join(latest_project_folder, 'weights', 'best.pt')  # e.g. /home/tbrain2/Software/YoloV5RWM/runs/train/igis_2022-11-03_13-38-41/weights/best.pt
    print("copy %s to %s" % (best_weightfile, model_dir))
    copy_smart(best_weightfile, model_dir, overwrite=False, dry_run=False)
    return best_weightfile
def make_model_files(
        session_name: str,
        version: Optional[int]) -> str:
    # Make folder for the model files
    print(session_name)
    model_file_suffix = 'YOLOv5' + '_V%s' % version if version is not None else ''
    model_dir_name = session_name + '_'+ model_file_suffix
    model_dir = os.path.join(RELEASED_MODEL_DIR, model_dir_name)
    print(model_dir)
    mkdir_p(model_dir)
    # Make Model_json.json
    make_model_json(model_dir, version)
    # Copy weights 
    copy_weights(session_name, model_dir)
    return model_dir
 
def update_database(
        database_name: str, 
        file_path: str,
        version: Optional[int]):
    rwm_db = RoboWeedMaPSDB(db=database_name)
    rwm_db.insert_ml_model(
        model_type=MODEL_TYPE, 
        description='RWM YOLOv5' + ' V%s' % version if version is not None else '',  
        file_name=os.path.basename(file_path))
def main(args=None):
    # Parse arguments      
    args = parse_args(args)
    version = args.version
    publish_to_test = args.publish_to_test
    publish_to_prod = args.publish_to_prod
    # Find name for this trainnig session
    session_name = get_training_session_name()
    # Make folder with files for the model on NAS
    model_dir = make_model_files(session_name, version)
    # Publish database(s)
    if publish_to_test:
        update_database(TEST_DATABASE_NAME, model_dir, version)
    
    if publish_to_prod:
        update_database(PROD_DATABASE_NAME, model_dir, version)  
if __name__ == "__main__":
    main(args = sys.argv[1:])
