#!/usr/bin/env python
import os
import shutil
import time
from typing import Any, Dict, List, Literal, Optional
import numpy as np
from tqdm import tqdm
from AgroDB import RoboWeedMaPSDB
from ImageCache import AnnotationImageCache
from Misc.path import suffix, mkdir_p, copy_smart, symlink_smart
from Misc.geometry import center_enclosed
from Conf.ml_data_info import make_blacklist_plant_ids_annotation_csv
EPPO_CODES = [
     'PPPMM'  # Dicot
    ,'PPPDD'  # Monocot
    ,'VICFX'  # Faba bean
    ,'PIBSA'  # Field Pea
    ,'ZEAMX'  # Maize
    ,'SOLTU'  # Potato
    ,'SPQOL'  # Spinach
    ,'BEAVA'  # Sugar beet
    ,'CIRAR'  # Creeping Thistle
    ,'BRSOL'  # White cabbage
    ,'FAGES'  # Buckwheat
    ,'1LUPG'  # Lupinus
    ,'PSEZ'   # Plant Stem Emergence Zone (Not a real EPPO code)
]  # Eppo code for the plants that we use as labels
IMAGE_IDS_HELD_BACK = [
    # OpenDR
    831621, 971110, 971112, 984201, 1028464, 1028465, 1028466, 1030259, 1030260, 1030261, 1030262,
    1030263, 1030275, 1038335, 1038338, 1038340, 1038348, 1046441, 1059091, 1074250, 1266069, 1473,
    1517, 19837, 45622, 78778, 78875, 79120, 79380, 80002, 199258, 200798, 201079, 209084, 210169,
    211563, 221553, 200955, 201061, 201180, 201662, 205943, 200519, 19980, 211360, 219383, 223811,
    237549, 238292, 238343, 238383, 238454, 238505, 263806, 264662, 276765, 269462, 269691, 454059,
    457756, 616407, 698894, 700239, 705775, 719534, 719787, 724635, 728245, 728516, 728623, 730457,
    731186, 719223, 720530, 723601, 724594, 724964, 727433, 727578, 728021, 728160, 728682, 729222,
    729406, 729424, 729799, 729949, 731542, 731753, 731797, 732787, 750833, 1039580, 1039975, 1046361,
    1048482, 1051783, 1325024, 1327434, 1351743, 1424694, 1424985, 1438760, 1441727, 1449518, 727983,
    677352, 666085, 704127, 680718, 701640, 1131874, 1131927, 1131968, 1131908, 1131949, 1131951,
    1131970, 1131884, 1448140, 1448159, 1448191, 1449134, 1448215, 1448241, 1448277, 1448310, 1448355,
    1448380, 1448426, 1448442, 1448815
]
# Force images from this upload into the training bucket
FIXED_UPLOAD_IDS_TRAIN = [773,775,776,777,778,779]  # 2020-10-09 Oekotek - we also fix grown for train
FIXED_UPLOAD_IDS_VAL = []
FIXED_UPLOAD_IDS_TEST = []
FIXED_IMAGE_IDS_TRAIN = []  
FIXED_IMAGE_IDS_VAL = []
FIXED_IMAGE_IDS_TEST = [  # Images also found in Test/Debug upload 355 
    3, 4, 849, 462, 3411, 3412, 3414, 3417, 3420, 3567, 3569, 3574, 3576, 3579, 4137, 4140, 
    9758, 20542, 20544, 20546, 20547, 20549, 22013, 22551, 22552, 23562, 23617, 67060, 67062, 
    67066, 67374, 76818, 77634, 78653, 78654, 78655, 95304, 95496, 238939, 238941, 238942, 376823, 
    376824, 376825, 828075, 850670]  # ToDo: Automate fetch this and make new test upload just for this purpose
""""
/****** Get image ids for original images in test upload 355******/
SELECT [Id] AS [ImageId], UploadId
FROM [data].[Images]
WHERE [FileName] in (SELECT [FileName] FROM [data].[Images] WHERE UploadId = 355) AND UploadId != 355
ORDER BY UploadId, Id
"""  
# Const
DATABASE_NAME = 'RoboWeedMaps'  # Must be production, we can only train on production code!
WORK_DIR_NAME = 'data'  # Folder for the train, val and test files
DATA_CONFIG_YAML_FILENAME = 'dataset.yaml' # data-configurations yaml file (used by YoloV5 train.py)
# Paths
src_dir = os.path.abspath(os.path.join(__file__, os.pardir))
training_session_dir = os.path.abspath(os.path.join(src_dir, os.pardir))
work_dir = os.path.realpath(os.path.join(training_session_dir, WORK_DIR_NAME))
images_dir = os.path.join(work_dir, 'images')
train_images_dir = os.path.join(images_dir, 'train')
val_images_dir = os.path.join(images_dir, 'val')
test_images_dir = os.path.join(images_dir, 'test')
labels_dir = os.path.join(work_dir, 'labels')
train_labels_dir = os.path.join(labels_dir, 'train')
val_labels_dir = os.path.join(labels_dir, 'val')
test_labels_dir = os.path.join(labels_dir, 'test')
bucket_image_paths = [
    train_images_dir
    ,val_images_dir
    ,test_images_dir
]
BUCKET_PROB = np.array([0.80, 0.20, 0.0])
def reset_work_dir():
    print("Reset work dir: %s .." % work_dir)
    # Remove old work dir
    old_work_dir = suffix(work_dir)
    if os.path.exists(old_work_dir):
        shutil.move(old_work_dir, '/tmp/')
    # Remake the work dir
    mkdir_p(work_dir)
    # Make the training images dirs
    mkdir_p(train_images_dir)
    mkdir_p(val_images_dir)
    mkdir_p(test_images_dir)
    # Make the training labels dirs
    mkdir_p(train_labels_dir)
    mkdir_p(val_labels_dir)
    mkdir_p(test_labels_dir)
def make_data_config_file() -> str:
    yaml_path = os.path.join(work_dir, DATA_CONFIG_YAML_FILENAME)
    with open(yaml_path, 'w') as fp:
        # Write labels
        fp.write("names:" + os.linesep)
        fp.writelines(["- %s%s" % (eppo, os.linesep) for eppo in EPPO_CODES])
        # Write number of classes
        fp.write("nc: %d%s" % (len(EPPO_CODES), os.linesep))
        # Write folder paths
        fp.writelines([
            "train: %s%s" % (train_images_dir, os.linesep)
            ,"val: %s%s" % (val_images_dir, os.linesep)
            ,"test: %s%s" % (test_images_dir, os.linesep)
        ]) 
    return yaml_path
def fetch_db_data():
    print("Fetch annotation data from db..")
    # SQL driver for RoboWeedMaPS database
    rwm_db = RoboWeedMaPSDB(db=DATABASE_NAME)
    # Fetch the basis data
    print("Fetch the basis data..")
    data = rwm_db.get_labled_data_annotation()
    # Filter out the held back images
    print("Filter out the held back images..")
    before_len = len(data)
    data = [row for row in tqdm(data) if row['ImageId'] not in IMAGE_IDS_HELD_BACK ]
    print(f"{before_len} -> {len(data)}")
    # Filter PSEZ
    print("Filter PSEZ..")
    skip_count = 0
    data_filtered = []
    for row_i in tqdm(data):
        if row_i['EPPOCode'] == 'PSEZ':
            psez_image_id = row_i['ImageId']
            match_found = False
            for row_j in data:
                # For PSEZ check if they are inside an other bounding box of type Maize (ZEAMX), Sugar Beet (BEAVA) or White Cabbage (BRSOL) 
                if row_j['ImageId'] == psez_image_id:
                    if row_j['EPPOCode'] in ('ZEAMX', 'BEAVA', 'BRSOL'):  # Selected crops to find PSEZ for
                        if center_enclosed(
                            inner_box=np.array([row_i['MinX'], row_i['MinY'], row_i['MaxX'], row_i['MaxY']]), # PSEZ box
                            outer_box=np.array([row_j['MinX'], row_j['MinY'], row_j['MaxX'], row_j['MaxY']])  # Plant box ie. ZEAMX, BEAVA or BRSOL 
                        ): 
                            print("%s (%s) --> %s (%s)" %(row_i['Id'], row_i['EPPOCode'], row_j['Id'], row_j['EPPOCode']))
                            data_filtered.append(row_i)
                            match_found = True
                            break
            if not match_found:
                # This PSEZ inn't enclosed by any crop bbox
                skip_count += 1
                print("Skip PSEZ: %s" % row_i['Id'])
        else:
            data_filtered.append(row_i)  # Add all other rows than PSEZ
    print("Total number of annotations: %d" % len(data_filtered))
    print("PSEZ skipped : %s" % skip_count)
    return data_filtered
def partion_on_image_id(db_data) -> Dict:
    print("Partion annotation data on file names")
    result = {}
    for d in tqdm(db_data):
        image_id = d['ImageId']
        if image_id not in result:
            result[image_id] = []
        result[image_id].append(d)
    print("Total number of images: %d" % len(result.keys()))
    return result
def get_bucket_path(data_rows) -> str:
    data_row = data_rows[0] 
    upload_id: int = data_row['UploadId']
    grown_weed = data_row['GrownWeed']
    # Option to fix uploads to bucket
    if upload_id in FIXED_UPLOAD_IDS_TRAIN:
        return train_images_dir
    elif upload_id in FIXED_UPLOAD_IDS_VAL:
        return val_images_dir
    elif upload_id in FIXED_UPLOAD_IDS_TEST:
        return test_images_dir
    
    # Option to fix images to bucket
    if upload_id in FIXED_IMAGE_IDS_TRAIN:
        return train_images_dir
    elif upload_id in FIXED_IMAGE_IDS_VAL:
        return val_images_dir
    elif upload_id in FIXED_IMAGE_IDS_TEST:
        return test_images_dir
    
    # Fix grown images e.g. plant boxes from Flakkebjerg, to train 
    # These images are not target, but we can learn visual plant features 
    if grown_weed:
        return train_images_dir
    # Distrubte at random
    return np.random.choice(bucket_image_paths, p=BUCKET_PROB / BUCKET_PROB.sum())
    
def make_image_file(
            annotation_cache: AnnotationImageCache,
            data_rows: List[Dict[str, Any]]
        ) -> str:
    data_row = data_rows[0]
    image_id = data_row['ImageId']
    upload_id=data_row['UploadId']
    filename=data_row['FileName']
    # Fetch image to local storage
    image_local_path = annotation_cache.get_path(upload_id, filename)
    # Find if image is train, val or test
    bucket_path: str = get_bucket_path(data_rows)
    # make sym link to image
    _, ext = os.path.splitext(filename)
    image_link_path: str = os.path.join(bucket_path, str(image_id)+ext)
    os.symlink(image_local_path, image_link_path)
    return image_link_path
# Find the eppo codes from anotation to root, that are labels
def find_relevant_eppo(eppo_code: str, cotyledon_id: int) -> Optional[str]:
    # handle SOLTU[DIGIT] and SPQOL[DIGIT]
    for EPPO_CODE in EPPO_CODES:
        if eppo_code.startswith(EPPO_CODE):
            eppo_code = EPPO_CODE
    # find the eppo code to use
    if eppo_code in EPPO_CODES:
        return eppo_code
    elif cotyledon_id == -100:
        return 'PPPMM'
    elif cotyledon_id == -101:
        return 'PPPDD'
    else:    
        return None
def row_to_coco(row: Dict[str, Any]) -> Optional[str]:
    eppo_code = row['EPPOCode']
    cotyledon_id = row['cotyledon']
    min_x = row['MinX']
    min_y = row['MinY']
    max_x = row['MaxX']
    max_y = row['MaxY']
    image_width = row['Width']
    image_height = row['Height']
    # YOLO labeling format
    # <class-ID> <X center> <Y center> <Box width> <Box height>
    # Values are nomalized from zero to one
    if eppo_code is None:
        return None
    eppo_code = find_relevant_eppo(eppo_code, cotyledon_id)
    if eppo_code is None:
        return None
    
    class_index = EPPO_CODES.index(eppo_code)
    box_width =  max_x - min_x
    box_height =  max_y - min_y
    center_x = float(box_width)/2 + min_x
    center_y = float(box_height)/2 + min_y
    center_x_norm = center_x / float(image_width)
    center_y_norm = center_y / float(image_height)
    box_width_norm = box_width / float(image_width)
    box_height_norm = box_height / float(image_height)
    return '%s %s %s %s %s' % (
        class_index 
        ,center_x_norm
        ,center_y_norm
        ,box_width_norm
        ,box_height_norm)
def label_file_content(data_rows: List[Dict[str, Any]]) -> List[str]:
    result = []
    for row in data_rows:
        coco = row_to_coco(row)
        if coco is not None:
            result.append(coco)
    return result
def make_label_file(
            image_path: str,
            data_rows: List[Dict[str, Any]]
        ) -> str:
    # Find labels file path
    images_dir, image_filename = os.path.split(image_path)
    image_name, _ = os.path.splitext(image_filename)
   
    labels_dir = 'labels'.join(images_dir.rsplit('images', 1))
    label_file_path = os.path.join(labels_dir, image_name + '.txt')
    # Write labels content to file
    with open(label_file_path, 'w') as fp:
        fp.writelines([line + os.linesep for line in label_file_content(data_rows) if line])
    return label_file_path
def make_dataset(image_data: Dict[str, List[Dict[str, Any]]]):
    # Local image Handler
    annotation_cache = AnnotationImageCache()
    progress_bar : tqdm = tqdm(image_data.items())
    for image_id, data_rows in progress_bar:
        progress_bar.set_description("ImageId: %d" % image_id)
        bucket_path:str = get_bucket_path(data_rows)
        # Make Image file and link to this
        image_link_path = make_image_file(annotation_cache, data_rows)
        # Make label file
        make_label_file(image_link_path, data_rows)
    
def make_yolov5_datasets():
    print("Make working directory..")
    reset_work_dir()
    print("Make info files..")
    make_blacklist_plant_ids_annotation_csv(work_dir)
    
    print("Make the config files..")
    data_config_path = make_data_config_file()
    print("Fetch data from database..")
    start_time = time.time()
    db_data: List[Dict[str, Any]] = fetch_db_data()
    data_pr_image: Dict[str, List[Dict[str, Any]]] = partion_on_image_id(db_data)
    print("Done fetching data in %d seconds" % (time.time() - start_time))
    print("Make image files and labels")
    start_time = time.time()
    make_dataset(data_pr_image)
    print("Done processing data in %d seconds" % (time.time() - start_time))
    
if __name__ == "__main__":
    
    make_yolov5_datasets()  # Make custom_data.yaml 
    print("YoloV5 datasets done")
