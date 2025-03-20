import os
import numpy as np
from collections import defaultdict
from db import fetch_annotations, fetch_image_info

EPPO_CODES = ['PPPMM','PPPDD','VICFX','PIBSA','ZEAMX','SOLTU','SPQOL','BEAVA','CIRAR','BRSOL','FAGES','1LUPG','PSEZ']
IMAGE_IDS_HELD_BACK = {831621,971110,971112,984201,1028464,1028465,1028466,1030259,1030260,1030261,1030262,
                       1030263,1030275,1038335,1038338,1038340,1038348,1046441,1059091,1074250,1266069,1473,
                       1517,19837,45622,78778,78875,79120,79380,80002,199258,200798,201079,209084,210169,
                       211563,221553,200955,201061,201180,201662,205943,200519,19980,211360,219383,223811,
                       237549,238292,238343,238383,238454,238505,263806,264662,276765,269462,269691,454059,
                       457756,616407,698894,700239,705775,719534,719787,724635,728245,728516,728623,730457,
                       731186,719223,720530,723601,724594,724964,727433,727578,728021,728160,728682,729222,
                       729406,729424,729799,729949,731542,731753,731797,732787,750833,1039580,1039975,1046361,
                       1048482,1051783,1325024,1327434,1351743,1424694,1424985,1438760,1441727,1449518,727983,
                       677352,666085,704127,680718,701640,1131874,1131927,1131968,1131908,1131949,1131951,
                       1131970,1131884,1448140,1448159,1448191,1449134,1448215,1448241,1448277,1448310,1448355,
                       1448380,1448426,1448442,1448815}

def filter_annotations(annotations):
    filtered = [a for a in annotations if a['ImageId'] not in IMAGE_IDS_HELD_BACK]
    data = []
    for row in filtered:
        if row['EPPOCode'] == 'PSEZ':
            img_id = row['ImageId']
            match = False
            for r in filtered:
                if r['ImageId'] == img_id and r['EPPOCode'] in ('ZEAMX','BEAVA','BRSOL'):
                    box_inner = np.array([row['MinX'], row['MinY'], row['MaxX'], row['MaxY']])
                    box_outer = np.array([r['MinX'], r['MinY'], r['MaxX'], r['MaxY']])
                    if center_in_box(box_inner, box_outer):
                        data.append(row)
                        match = True
                        break
            if not match:
                continue
        else:
            data.append(row)
    return data

def center_in_box(inner, outer):
    cx = (inner[0] + inner[2]) / 2
    cy = (inner[1] + inner[3]) / 2
    return outer[0] < cx < outer[2] and outer[1] < cy < outer[3]

def group_by_image(annotations):
    grouped = defaultdict(list)
    for row in annotations:
        grouped[row['ImageId']].append(row)
    return grouped

def convert_to_yolo(annotation, image_dims):
    eppo = annotation['EPPOCode']
    for code in EPPO_CODES:
        if eppo.startswith(code):
            eppo = code
    if eppo not in EPPO_CODES:
        return None
    class_index = EPPO_CODES.index(eppo)
    box_w = annotation['MaxX'] - annotation['MinX']
    box_h = annotation['MaxY'] - annotation['MinY']
    cx = annotation['MinX'] + box_w / 2.0
    cy = annotation['MinY'] + box_h / 2.0
    iw, ih = image_dims
    return f"{class_index} {cx/iw:.6f} {cy/ih:.6f} {box_w/iw:.6f} {box_h/ih:.6f}"

def create_label_file(image_path, annotations):
    from PIL import Image
    im = Image.open(image_path)
    iw, ih = im.size
    im.close()
    lines = []
    for a in annotations:
        line = convert_to_yolo(a, (iw,ih))
        if line is not None:
            lines.append(line)
    return lines
