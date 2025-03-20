import os
import sys
import argparse
from pathlib import Path

def parse_args():
    parser = argparse.ArgumentParser(description='Train YOLOv11 model on RWM dataset')
    parser.add_argument('--data', type=str, default='./datasets/rwm_yolov11/dataset.yaml', help='Path to dataset YAML file')
    parser.add_argument('--weights', type=str, default='yolov11n.pt', help='Initial weights')
    parser.add_argument('--img-size', type=int, default=1600, help='Image size for training')
    parser.add_argument('--batch-size', type=int, default=8, help='Batch size')
    parser.add_argument('--epochs', type=int, default=100, help='Number of epochs')
    parser.add_argument('--device', type=str, default='0', help='Device to use (e.g., cuda device)')
    parser.add_argument('--project', type=str, default='runs/train', help='Project directory')
    parser.add_argument('--name', type=str, default='rwm_yolov11', help='Run name')
    return parser.parse_args()

def main():
    args = parse_args()
    
    print(f"Starting YOLOv11 training on RWM dataset...")
    print(f"Dataset: {args.data}")
    print(f"Weights: {args.weights}")
    print(f"Image size: {args.img_size}")
    print(f"Batch size: {args.batch_size}")
    print(f"Epochs: {args.epochs}")
    print(f"Device: {args.device}")
    
    # Import ultralytics here to avoid loading it until needed
    try:
        from ultralytics import YOLO
    except ImportError:
        print("Error: Ultralytics package not found. Please install it with 'pip install ultralytics'.")
        sys.exit(1)
    
    # Load model
    model = YOLO(args.weights)
    
    # Start training
    model.train(
        data=args.data,
        imgsz=args.img_size,
        batch=args.batch_size,
        epochs=args.epochs,
        device=args.device,
        project=args.project,
        name=args.name
    )
    
    print("Training complete!")

if __name__ == '__main__':
    main()