#!/usr/bin/env python
import json

def main():
    args = {
      "project_name": "YOLOv11_CropWeed",
      "data": {
        "train": "/data/rwm_dataset/data/images/train",
        "val": "/data/rwm_dataset/data/images/val",
        "test": "/data/rwm_dataset/data/images/test"
      },
      "labels": {
        "train": "/data/rwm_dataset/data/labels/train",
        "val": "/data/rwm_dataset/data/labels/val",
        "test": "/data/rwm_dataset/data/labels/test"
      },
      "num_classes": 13,
      "class_names": [
        "PPPMM",
        "PPPDD",
        "VICFX",
        "PIBSA",
        "ZEAMX",
        "SOLTU",
        "SPQOL",
        "BEAVA",
        "CIRAR",
        "BRSOL",
        "FAGES",
        "1LUPG",
        "PSEZ"
      ],
      "training_params": {
        "batch_size": 16,
        "img_size": 640,
        "epochs": 50,
        "learning_rate": 0.001,
        "device": "cuda:0"
      }
    }
    with open("train_args.json", "w") as f:
        json.dump(args, f, indent=4)
    print("Training configuration ARGS file 'train_args.json' generated.")

if __name__ == "__main__":
    main()
