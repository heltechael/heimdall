#!/usr/bin/env python3
import os
import argparse
import yaml
from datetime import datetime
from ultralytics import YOLO

def parse_args():
    parser = argparse.ArgumentParser(description='Train YOLOv11 on RoboWeedMaPS dataset')
    
    parser.add_argument('--dataset', '-d', type=str, required=True,
                      help='Path to the YOLO dataset directory containing dataset.yaml')
    parser.add_argument('--epochs', '-e', type=int, default=100,
                      help='Number of epochs to train for (default: 100)')
    parser.add_argument('--batch', '-b', type=int, default=16,
                      help='Batch size (default: 16)')
    parser.add_argument('--img-size', '-s', type=int, default=1280,
                      help='Image size for training (default: 1280)')
    parser.add_argument('--weights', '-w', type=str, default='yolov11l.pt',
                      help='Initial weights (default: yolov11l.pt)')
    parser.add_argument('--device', type=str, default='0',
                      help='CUDA device (default: 0)')
    parser.add_argument('--name', type=str, default=None,
                      help='Name for this training run (default: auto-generated)')
    parser.add_argument('--patience', type=int, default=50,
                      help='Early stopping patience (default: 50)')
    
    return parser.parse_args()

def main():
    args = parse_args()
    
    yaml_path = os.path.join(args.dataset, 'dataset.yaml')
    if not os.path.exists(yaml_path):
        print(f"Error: dataset.yaml not found at {yaml_path}")
        return
    
    with open(yaml_path, 'r') as f:
        dataset_config = yaml.safe_load(f)
    
    print(f"Dataset loaded: {len(dataset_config['names'])} classes")
    print(f"Classes: {dataset_config['names']}")
    
    if args.name is None:
        timestamp = datetime.now().strftime('%Y-%m-%d_%H-%M-%S')
        args.name = f"rwm_yolov11_{timestamp}"
    
    output_dir = os.path.join("runs", "train", args.name)
    os.makedirs(output_dir, exist_ok=True)
    
    model = YOLO(args.weights)
    
    results = model.train(
        data=yaml_path,
        epochs=args.epochs,
        batch=args.batch,
        imgsz=args.img_size,
        device=args.device,
        name=args.name,
        patience=args.patience,
        verbose=True
    )
    
    print(f"Training completed! Results saved to {output_dir}")

if __name__ == "__main__":
    main()
