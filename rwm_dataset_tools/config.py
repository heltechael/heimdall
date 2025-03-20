import argparse

def get_args():
    parser = argparse.ArgumentParser()
    parser.add_argument("--output-dir", type=str, required=True)
    parser.add_argument("--model-format", type=str, choices=["yolov5", "yolov11"], default="yolov11")
    parser.add_argument("--train-split", type=float, default=0.8)
    parser.add_argument("--val-split", type=float, default=0.2)
    parser.add_argument("--db-server", type=str, default="localhost")
    parser.add_argument("--db-name", type=str, default="RoboWeedMaps")
    parser.add_argument("--db-user", type=str, default="SA")
    parser.add_argument("--db-password", type=str, default="Robotbil123!")
    return parser.parse_args()
