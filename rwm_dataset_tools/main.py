import os
import time
from config import get_args
from db import get_connection, fetch_annotations, fetch_image_info
from dataset_extractor import filter_annotations, group_by_image, create_label_file
from image_linker import link_image, write_label_file

def main():
    args = get_args()
    conn = get_connection(args.db_server, args.db_name, args.db_user, args.db_password)
    annotations = fetch_annotations(conn)
    images = fetch_image_info(conn)
    conn.close()
    annots = filter_annotations(annotations)
    grouped = group_by_image(annots)
    os.makedirs(os.path.join(args.output_dir, "images"), exist_ok=True)
    os.makedirs(os.path.join(args.output_dir, "labels"), exist_ok=True)
    image_dict = {img['Id']: img for img in images}
    for image_id, ann_list in grouped.items():
        img_info = image_dict.get(image_id)
        if img_info is None:
            continue
        src_path = os.path.join("/data/roboweedmaps/images", str(img_info['UploadId']), img_info['FileName'])
        img_link = link_image(src_path, os.path.join(args.output_dir, "images"), image_id)
        labels = create_label_file(img_link, ann_list)
        write_label_file(labels, os.path.join(args.output_dir, "labels"), image_id)
    create_yaml_config(args)

def create_yaml_config(args):
    import yaml
    config = {
        "train": os.path.join(args.output_dir, "images"),
        "val": os.path.join(args.output_dir, "images"),
        "nc":  len(["PPPMM","PPPDD","VICFX","PIBSA","ZEAMX","SOLTU","SPQOL","BEAVA","CIRAR","BRSOL","FAGES","1LUPG","PSEZ"]),
        "names": ["PPPMM","PPPDD","VICFX","PIBSA","ZEAMX","SOLTU","SPQOL","BEAVA","CIRAR","BRSOL","FAGES","1LUPG","PSEZ"]
    }
    yaml_path = os.path.join(args.output_dir, "dataset.yaml")
    with open(yaml_path, "w") as f:
        yaml.dump(config, f)
    
if __name__ == "__main__":
    start = time.time()
    main()
    print(time.time()-start)
