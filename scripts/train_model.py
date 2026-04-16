"""
YOLOv8 Model Training Script for Short-Chain Commerce.

This script trains a YOLOv8 object detection model on the generated mock dataset.
"""

import argparse
import json
import os
import sys
from pathlib import Path
from typing import Dict, List, Tuple

# Fix OpenMP duplicate library issue
os.environ['KMP_DUPLICATE_LIB_OK'] = 'TRUE'

import cv2
import numpy as np
from ultralytics import YOLO


class YOLODatasetConverter:
    """Convert JSON annotations to YOLO format."""

    # Define class IDs for our products
    CLASS_NAMES = [
        "tomato",
        "lettuce",
        "carrot",
        "pepper",
        "onion",
        "potato",
        "cucumber",
        "broccoli",
    ]

    def __init__(self, data_dir: str):
        self.data_dir = Path(data_dir)
        self.class_to_id = {name: idx for idx, name in enumerate(self.CLASS_NAMES)}

    def convert_to_yolo_format(self, annotations_file: str, output_dir: str):
        """
        Convert JSON annotations to YOLO format.

        Args:
            annotations_file: Path to JSON annotations file
            output_dir: Directory to save YOLO format files
        """
        output_dir = Path(output_dir)
        output_dir.mkdir(parents=True, exist_ok=True)

        # Load annotations
        with open(annotations_file, 'r') as f:
            annotations = json.load(f)

        for ann in annotations:
            image_id = ann['image_id']
            image_path = Path(ann['image_path'])
            width = ann['width']
            height = ann['height']

            # Read image to verify it exists
            if not image_path.exists():
                print(f"Warning: Image not found: {image_path}")
                continue

            # Create YOLO label file
            label_file = output_dir / f"{image_id}.txt"

            # For mock data, we'll create bounding boxes for each product
            # In real scenario, you'd have explicit bounding box coordinates
            products = ann['metadata']['products']

            # Generate bounding boxes based on image grid (mock data limitation)
            with open(label_file, 'w') as lf:
                num_products = len(products)
                cols = 4
                rows = (num_products + cols - 1) // cols
                cell_w = 680 / cols
                cell_h = 480 / rows

                for i, product_name in enumerate(products):
                    class_id = self.class_to_id.get(product_name.lower(), 0)

                    # Calculate centered position in cell
                    row = i // cols
                    col = i % cols

                    center_x_rel = (60 + col * cell_w + cell_w // 2) / width
                    center_y_rel = (60 + row * cell_h + cell_h // 2) / height

                    # Random size (normalized)
                    size_rel = np.random.uniform(0.1, 0.2)

                    w_rel = size_rel
                    h_rel = size_rel

                    lf.write(f"{class_id} {center_x_rel:.6f} {center_y_rel:.6f} {w_rel:.6f} {h_rel:.6f}\n")

        print(f"Converted {len(annotations)} annotations to YOLO format")

    def create_yaml_config(self, train_dir: str, val_dir: str, test_dir: str, output_path: str):
        """
        Create YOLO dataset YAML configuration.

        Args:
            train_dir: Path to training images directory
            val_dir: Path to validation images directory
            test_dir: Path to test images directory
            output_path: Path to save YAML config
        """
        yaml_content = f"""# Short-Chain Commerce Dataset Configuration
# Generated for YOLOv8 object detection

path: {self.data_dir.parent / 'yolo_dataset'}  # dataset root directory
train: {train_dir}  # train images (relative to path)
val: {val_dir}  # val images (relative to path)
test: {test_dir}  # test images (relative to path)

# Classes
names:
{chr(10).join(f'  {i}: {name}' for i, name in enumerate(self.CLASS_NAMES))}

# Dataset information
nc: {len(self.CLASS_NAMES)}  # number of classes
roboflow:
  license: MIT
  project: short-chain-commerce
  version: 1.0
  wrap: false
"""

        with open(output_path, 'w') as f:
            f.write(yaml_content)

        print(f"Created dataset YAML: {output_path}")


def train_model(
    data_yaml: str,
    epochs: int = 50,
    batch_size: int = 16,
    imgsz: int = 640,
    model_type: str = "yolov8n",
    project: str = "runs/detect",
    name: str = "exp",
):
    """
    Train YOLOv8 model.

    Args:
        data_yaml: Path to dataset YAML configuration
        epochs: Number of training epochs
        batch_size: Batch size
        imgsz: Image size
        model_type: YOLO model type (yolov8n, yolov8s, yolov8m, etc.)
        project: Project directory for outputs
        name: Experiment name
    """
    # Load pretrained model
    model = YOLO(f"{model_type}.pt")

    # Start training
    results = model.train(
        data=data_yaml,
        epochs=epochs,
        batch=batch_size,
        imgsz=imgsz,
        project=project,
        name=name,
        device="cpu",  # Use CPU (no GPU available)
        workers=0,
        patience=10,  # Early stopping patience
        lr0=0.01,  # Initial learning rate
        momentum=0.937,
        weight_decay=0.0005,
    )

    # Evaluate on validation set
    print("\nEvaluating on validation set...")
    metrics = model.val()

    print(f"\n=== Training Complete ===")
    print(f"mAP50: {metrics.box.map50:.4f}")
    print(f"mAP50-95: {metrics.box.map:.4f}")
    print(f"Precision: {metrics.box.mp:.4f}")
    print(f"Recall: {metrics.box.mr:.4f}")

    # Export model
    export_path = model.export(format="onnx")
    print(f"\nModel exported to: {export_path}")

    return results


def main():
    parser = argparse.ArgumentParser(description="Train YOLOv8 model for product detection")

    # Dataset preparation arguments
    parser.add_argument(
        "--convert",
        action="store_true",
        help="Convert annotations to YOLO format",
    )
    parser.add_argument(
        "--data_dir",
        type=str,
        default="data/raw",
        help="Path to raw data directory",
    )

    # Training arguments
    parser.add_argument(
        "--epochs",
        type=int,
        default=50,
        help="Number of training epochs",
    )
    parser.add_argument(
        "--batch_size",
        type=int,
        default=16,
        help="Batch size",
    )
    parser.add_argument(
        "--imgsz",
        type=int,
        default=640,
        help="Image size",
    )
    parser.add_argument(
        "--model_type",
        type=str,
        default="yolov8n",
        choices=["yolov8n", "yolov8s", "yolov8m", "yolov8l"],
        help="YOLO model type",
    )

    args = parser.parse_args()

    # Step 1: Convert annotations to YOLO format
    data_dir = Path(args.data_dir)

    # Create directories for YOLO format
    yolo_dir = data_dir.parent / "yolo_dataset"
    yolo_dir.mkdir(exist_ok=True)

    images_dir = yolo_dir / "images"
    labels_dir = yolo_dir / "labels"
    (images_dir / "train").mkdir(parents=True, exist_ok=True)
    (images_dir / "val").mkdir(parents=True, exist_ok=True)
    (images_dir / "test").mkdir(parents=True, exist_ok=True)
    (labels_dir / "train").mkdir(parents=True, exist_ok=True)
    (labels_dir / "val").mkdir(parents=True, exist_ok=True)
    (labels_dir / "test").mkdir(parents=True, exist_ok=True)

    # Copy images and convert labels
    converter = YOLODatasetConverter(args.data_dir)

    # Process each split
    for split in ["train", "val", "test"]:
        ann_file = data_dir / f"{split}_annotations.json"
        if ann_file.exists():
            with open(ann_file, 'r') as f:
                anns = json.load(f)

            for ann in anns:
                image_id = ann['image_id']
                src_image = Path(ann['image_path'])
                dst_image = images_dir / split / f"{image_id}.jpg"

                if src_image.exists():
                    # Copy image
                    import shutil
                    shutil.copy(src_image, dst_image)

            # Convert labels for this split
            converter.convert_to_yolo_format(str(ann_file), str(labels_dir / split))

    # Create YAML config
    yaml_path = yolo_dir / "dataset.yaml"
    converter.create_yaml_config(
        train_dir="images/train",
        val_dir="images/val",
        test_dir="images/test",
        output_path=str(yaml_path),
    )

    # Step 2: Train the model
    print("\n" + "="*50)
    print("Starting model training...")
    print("="*50)

    train_model(
        data_yaml=str(yaml_path),
        epochs=args.epochs,
        batch_size=args.batch_size,
        imgsz=args.imgsz,
        model_type=args.model_type,
        project="runs/detect",
        name=f"{args.model_type}_exp",
    )


if __name__ == "__main__":
    main()
