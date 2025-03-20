import os
import shutil
import time
import numpy as np
from tqdm import tqdm
from config.dataset_config import DATABASE_NAME, BASE_DIR, BUCKET_PROB, FIXED_IMAGE_IDS_TEST, FIXED_IMAGE_IDS_TRAIN, FIXED_IMAGE_IDS_VAL, FIXED_UPLOAD_IDS_TRAIN, FIXED_UPLOAD_IDS_TEST, FIXED_UPLOAD_IDS_VAL, EPPO_CODES, IMAGE_IDS_HELD_BACK
from data_processing.db_connector import RoboWeedMaPSDB
from data_processing.annotation_utils import mkdir_p, suffix, AnnotationImageCache, center_enclosed, row_to_yolo

WORK_DIR_NAME = 'data'
DATA_CONFIG_YAML_FILENAME = 'dataset.yaml'

def reset_work_dir(work_dir):
    old_work_dir = suffix(work_dir)
    if os.path.exists(old_work_dir):
        shutil.move(old_work_dir, '/tmp/')
    mkdir_p(work_dir)
    images_dir = os.path.join(work_dir, 'images')
    labels_dir = os.path.join(work_dir, 'labels')
    for sub in ['train', 'val', 'test']:
        mkdir_p(os.path.join(images_dir, sub))
        mkdir_p(os.path.join(labels_dir, sub))
    return images_dir, labels_dir

def make_data_config_file(work_dir, train_images_dir, val_images_dir, test_images_dir):
    yaml_path = os.path.join(work_dir, DATA_CONFIG_YAML_FILENAME)
    with open(yaml_path, 'w') as fp:
        fp.write("names:\n")
        for code in EPPO_CODES:
            fp.write(f"- {code}\n")
        fp.write(f"nc: {len(EPPO_CODES)}\n")
        fp.write(f"train: {train_images_dir}\n")
        fp.write(f"val: {val_images_dir}\n")
        fp.write(f"test: {test_images_dir}\n")
    return yaml_path

def dummy_blacklist_csv(work_dir):
    path = os.path.join(work_dir, "blacklist.csv")
    with open(path, "w") as f:
        f.write("id\n")
    return path

def fetch_db_data():
    print("Fetch annotation data from db..")
    rwm_db = RoboWeedMaPSDB(db=DATABASE_NAME)
    print("Fetch the basis data..")
    data = rwm_db.get_labled_data_annotation()
    print("Filter out the held back images..")
    before_len = len(data)
    data = [row for row in data if row['ImageId'] not in IMAGE_IDS_HELD_BACK]
    print(f"{before_len} -> {len(data)}")
    print("Filter PSEZ..")
    skip_count = 0
    data_filtered = []
    for row_i in tqdm(data):
        if row_i['EPPOCode'] == 'PSEZ':
            psez_image_id = row_i['ImageId']
            match_found = False
            for row_j in data:
                if row_j['ImageId'] == psez_image_id and row_j['EPPOCode'] in ('ZEAMX', 'BEAVA', 'BRSOL'):
                    inner_box = np.array([row_i['MinX'], row_i['MinY'], row_i['MaxX'], row_i['MaxY']])
                    outer_box = np.array([row_j['MinX'], row_j['MinY'], row_j['MaxX'], row_j['MaxY']])
                    if center_enclosed(inner_box, outer_box):
                        data_filtered.append(row_i)
                        match_found = True
                        break
            if not match_found:
                skip_count += 1
                print(f"Skip PSEZ: {row_i['Id']}")
        else:
            data_filtered.append(row_i)
    print(f"Total number of annotations: {len(data_filtered)}")
    print(f"PSEZ skipped : {skip_count}")
    return data_filtered

def partition_by_image(db_data):
    result = {}
    for d in db_data:
        image_id = d['ImageId']
        if image_id not in result:
            result[image_id] = []
        result[image_id].append(d)
    print(f"Total number of images: {len(result.keys())}")
    return result

def get_bucket_path(data_rows, train_images_dir, val_images_dir, test_images_dir, bucket_image_paths):
    data_row = data_rows[0]
    upload_id = data_row['UploadId']
    grown_weed = data_row['GrownWeed']
    if upload_id in FIXED_UPLOAD_IDS_TRAIN:
        return train_images_dir
    elif upload_id in FIXED_UPLOAD_IDS_VAL:
        return val_images_dir
    elif upload_id in FIXED_UPLOAD_IDS_TEST:
        return test_images_dir
    if upload_id in FIXED_IMAGE_IDS_TRAIN:
        return train_images_dir
    elif upload_id in FIXED_IMAGE_IDS_VAL:
        return val_images_dir
    elif upload_id in FIXED_IMAGE_IDS_TEST:
        return test_images_dir
    if grown_weed:
        return train_images_dir
    return np.random.choice(bucket_image_paths, p=np.array(BUCKET_PROB)/np.sum(BUCKET_PROB))

def make_image_file(annotation_cache, data_rows, bucket_path):
    data_row = data_rows[0]
    image_id = data_row['ImageId']
    upload_id = data_row['UploadId']
    filename = data_row['FileName']
    image_local_path = annotation_cache.get_path(upload_id, filename)
    _, ext = os.path.splitext(filename)
    image_link_path = os.path.join(bucket_path, f"{image_id}{ext}")
    if not os.path.exists(image_link_path):
        os.symlink(image_local_path, image_link_path)
    return image_link_path

def make_label_file(image_path, data_rows, labels_dir):
    _, image_filename = os.path.split(image_path)
    image_name, _ = os.path.splitext(image_filename)
    label_file_path = os.path.join(labels_dir, image_name + '.txt')
    with open(label_file_path, 'w') as fp:
        lines = []
        for row in data_rows:
            line = row_to_yolo(row)
            if line:
                lines.append(line)
        fp.write("\n".join(lines))
    return label_file_path

def make_dataset(data_by_image, train_images_dir, val_images_dir, test_images_dir):
    bucket_image_paths = [train_images_dir, val_images_dir, test_images_dir]
    annotation_cache = AnnotationImageCache()
    images_base = os.path.join(os.path.dirname(train_images_dir), 'images')
    labels_base = os.path.join(os.path.dirname(train_images_dir), 'labels')
    for image_id, data_rows in tqdm(data_by_image.items(), desc="Processing images"):
        bucket_path = get_bucket_path(data_rows, train_images_dir, val_images_dir, test_images_dir, bucket_image_paths)
        image_link_path = make_image_file(annotation_cache, data_rows, bucket_path)
        subfolder = os.path.basename(bucket_path)
        label_folder = os.path.join(labels_base, subfolder)
        make_label_file(image_link_path, data_rows, label_folder)

def make_yolov11_datasets():
    base_dir = BASE_DIR
    work_dir = os.path.join(base_dir, WORK_DIR_NAME)
    print("Make working directory..")
    train_images_dir = os.path.join(work_dir, 'images', 'train')
    val_images_dir = os.path.join(work_dir, 'images', 'val')
    test_images_dir = os.path.join(work_dir, 'images', 'test')
    reset_work_dir(work_dir)
    print("Make info files..")
    dummy_blacklist_csv(work_dir)
    print("Make the config files..")
    make_data_config_file(work_dir, train_images_dir, val_images_dir, test_images_dir)
    print("Fetch data from database..")
    start_time = time.time()
    db_data = fetch_db_data()
    data_by_image = partition_by_image(db_data)
    print(f"Done fetching data in {time.time() - start_time} seconds")
    print("Make image files and labels")
    start_time = time.time()
    make_dataset(data_by_image, train_images_dir, val_images_dir, test_images_dir)
    print(f"Done processing data in {time.time() - start_time} seconds")

if __name__ == "__main__":
    make_yolov11_datasets()
    print("YOLOv11 datasets done")
