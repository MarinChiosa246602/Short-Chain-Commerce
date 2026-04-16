"""
Mock Dataset Generator for logistics data extraction.

This script generates labeled mock images for training and testing
the computer vision and OCR pipelines.

Usage:
    python scripts/generate_mock_data.py --num_images 500 --output_dir data/raw
"""

import argparse
import json
import os
import random
from datetime import datetime, timedelta
from pathlib import Path
from typing import List, Dict, Any, Optional

import numpy as np
from PIL import Image, ImageDraw, ImageFont


# Product types for mock data
PRODUCT_TYPES = [
    {"name": "Tomato", "color": (207, 16, 32), "size_range": (50, 80)},
    {"name": "Lettuce", "color": (34, 139, 34), "size_range": (70, 100)},
    {"name": "Carrot", "color": (237, 90, 20), "size_range": (30, 60)},
    {"name": "Pepper", "color": (0, 128, 0), "size_range": (60, 90)},
    {"name": "Onion", "color": (210, 180, 140), "size_range": (50, 75)},
    {"name": "Potato", "color": (210, 180, 140), "size_range": (45, 70)},
    {"name": "Cucumber", "color": (0, 100, 0), "size_range": (40, 70)},
    {"name": "Broccoli", "color": (0, 100, 0), "size_range": (80, 120)},
]

# Product names list for class indexing (must match order in train_model.py CLASS_NAMES)
PRODUCT_NAMES = [
    "tomato",
    "lettuce",
    "carrot",
    "pepper",
    "onion",
    "potato",
    "cucumber",
    "broccoli",
]

# Unit types
UNITS = ["crate", "box", "kg", "pallet"]

# Condition types
CONDITIONS = ["excellent", "good", "fair", "poor", "damaged"]

# Sample farm names
FARM_NAMES = [
    "Green Valley Farm",
    "Sunrise Agriculture",
    "Organic Harvest Co",
    "Family Farms LLC",
    "Fresh Fields Farm",
    "Organic Meadows",
    "Valley Fresh Produce",
]

# Sample destinations
DESTINATIONS = [
    "Downtown Market",
    "Community Center",
    "Restaurant Supply Co",
    "Farmers Market North",
    "Farmers Market South",
    "Distribution Center A",
    "Distribution Center B",
]


class MockImageGenerator:
    """Generate mock images for training."""

    def __init__(self, image_size: tuple = (800, 600)):
        """
        Initialize the generator.

        Args:
            image_size: Size of generated images (width, height)
        """
        self.image_size = image_size
        self.rng = np.random.RandomState(42)  # For reproducible bounding boxes

    def create_crate_image(
        self,
        products: List[Dict[str, Any]],
        quantity: int,
        condition: str = "excellent",
        label_text: Optional[str] = None,
    ) -> tuple[Image.Image, List[Dict]]:
        """
        Create a mock image of a crate with products.

        Args:
            products: List of product types to include
            quantity: Number of items in the crate
            condition: Product condition
            label_text: Optional label text to add

        Returns:
            Tuple of (PIL Image, list of bounding box data)
        """
        # Create background (crate)
        img = Image.new('RGB', self.image_size, color=(139, 119, 101))
        draw = ImageDraw.Draw(img)

        # Draw crate border
        draw.rectangle([50, 50, 750, 550], outline=(101, 67, 33), width=4)
        draw.rectangle([60, 60, 740, 540], outline=(139, 119, 101), width=2)

        # Calculate product positions
        num_products = min(len(products), quantity)
        cols = 4
        rows = (num_products + cols - 1) // cols
        cell_w = 680 // cols
        cell_h = 480 // rows

        bounding_boxes = []

        for i, product in enumerate(products[:quantity]):
            row = i // cols
            col = i % cols

            # Add random variation to position within cell (more realistic)
            jitter_x = self.rng.uniform(-30, 30)
            jitter_y = self.rng.uniform(-30, 30)

            center_x = 60 + col * cell_w + cell_w // 2 + jitter_x
            center_y = 60 + row * cell_h + cell_h // 2 + jitter_y

            # Adjust color based on condition
            product_color = product['color']
            if condition == 'damaged':
                product_color = tuple(max(0, c - 50) for c in product['color'])
            elif condition == 'poor':
                product_color = tuple(max(0, c - 30) for c in product['color'])

            # Draw product (circle for simplicity) with size variation
            base_size = random.randint(*product['size_range'])
            # Add depth variation (some products appear closer/larger)
            size_variation = self.rng.uniform(0.85, 1.15)
            size = int(base_size * size_variation)

            draw.ellipse(
                [center_x - size//2, center_y - size//2,
                 center_x + size//2, center_y + size//2],
                fill=product_color,
                outline=(50, 50, 50),
                width=2
            )

            # Store bounding box data
            bounding_boxes.append({
                'class': product['name'].lower(),
                'center_x': center_x,
                'center_y': center_y,
                'width': size,
                'height': size,
            })

        # Add label if provided
        if label_text:
            self._add_label(img, label_text)

        return img, bounding_boxes

    def _add_label(self, img: Image.Image, text: str):
        """Add a label to the image."""
        draw = ImageDraw.Draw(img)
        try:
            font = ImageFont.truetype("arial.ttf", 16)
        except:
            font = ImageFont.load_default()

        # Draw label background
        bbox = draw.textbbox((0, 0), text, font=font)
        label_w = bbox[2] - bbox[0] + 20
        label_h = bbox[3] - bbox[1] + 10

        draw.rectangle(
            [10, 10, 10 + label_w, 10 + label_h],
            fill=(255, 255, 255),
            outline=(0, 0, 0),
        )

        # Draw text
        draw.text((20, 15), text, fill=(0, 0, 0), font=font)

    def create_mixed_crate_image(
        self,
        num_products: int = 4,
        condition: str = "excellent",
    ) -> tuple:
        """
        Create a mock image of a mixed crate.

        Args:
            num_products: Number of different product types
            condition: Overall condition

        Returns:
            Tuple of (image, metadata, bounding_boxes)
        """
        # Select random products
        selected_products = random.sample(PRODUCT_TYPES, min(num_products, len(PRODUCT_TYPES)))

        quantity = random.randint(12, 36)

        # Generate label info
        product_names = [p['name'] for p in selected_products]
        label_text = f"{random.choice(FARM_NAMES)} | Qty: {quantity} | {random.choice(UNITS).upper()}"

        img, bounding_boxes = self.create_crate_image(
            products=selected_products,
            quantity=quantity,
            condition=condition,
            label_text=label_text,
        )

        metadata = {
            "products": product_names,
            "quantity": quantity,
            "condition": condition,
            "farm": random.choice(FARM_NAMES),
            "destination": random.choice(DESTINATIONS),
            "temperature": round(random.uniform(2, 10), 1),
            "humidity": round(random.uniform(70, 95), 1),
        }

        return img, metadata, bounding_boxes


class DatasetGenerator:
    """Generate complete labeled dataset."""

    def __init__(self, output_dir: str):
        """
        Initialize the dataset generator.

        Args:
            output_dir: Directory to save generated data
        """
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)

        # Create subdirectories
        (self.output_dir / "images").mkdir(exist_ok=True)
        (self.output_dir / "labels").mkdir(exist_ok=True)

        self.generator = MockImageGenerator()
        self.annotations = []

    def generate_dataset(
        self,
        num_images: int = 500,
        train_ratio: float = 0.7,
        val_ratio: float = 0.15,
        test_ratio: float = 0.15,
    ) -> Dict[str, str]:
        """
        Generate a complete labeled dataset.

        Args:
            num_images: Total number of images to generate
            train_ratio: Training set ratio
            val_ratio: Validation set ratio
            test_ratio: Test set ratio

        Returns:
            Dictionary with split file paths
        """
        print(f"Generating {num_images} mock images...")

        # Generate images with varying conditions
        for i in range(num_images):
            # Randomize parameters
            num_products = random.randint(1, 6)
            condition = random.choices(
                CONDITIONS,
                weights=[0.3, 0.35, 0.2, 0.1, 0.05],  # Bias toward good conditions
            )[0]

            # Generate image with bounding boxes
            img, metadata, bounding_boxes = self.generator.create_mixed_crate_image(
                num_products=num_products,
                condition=condition,
            )

            # Save image
            img_filename = f"img_{i:04d}.jpg"
            img_path = self.output_dir / "images" / img_filename
            img.save(img_path, quality=95)

            # Convert bounding boxes to YOLO format (normalized: class, x_center, y_center, width, height)
            yolo_boxes = []
            for bb in bounding_boxes:
                # Normalize coordinates to 0-1 range
                x_center_norm = bb['center_x'] / 800
                y_center_norm = bb['center_y'] / 600
                w_norm = bb['width'] / 800
                h_norm = bb['height'] / 600

                # Get class index (normalize to lowercase)
                class_name = bb['class'].lower()
                class_idx = PRODUCT_NAMES.index(class_name) if class_name in PRODUCT_NAMES else 0

                yolo_boxes.append(f"{class_idx} {x_center_norm:.6f} {y_center_norm:.6f} {w_norm:.6f} {h_norm:.6f}")

            # Save YOLO format label file
            label_txt_filename = f"img_{i:04d}.txt"
            label_txt_path = self.output_dir / "labels" / label_txt_filename
            with open(label_txt_path, 'w') as f:
                f.write('\n'.join(yolo_boxes))

            # Create annotation
            annotation = {
                "image_id": f"img_{i:04d}",
                "image_path": str(img_path),
                "split": self._get_split(i, num_images, train_ratio, val_ratio),
                "metadata": metadata,
                "width": 800,
                "height": 600,
                "bounding_boxes": yolo_boxes,
            }

            # Save individual annotation
            label_filename = f"img_{i:04d}.json"
            label_path = self.output_dir / "labels" / label_filename
            with open(label_path, 'w') as f:
                json.dump(annotation, f, indent=2)

            self.annotations.append(annotation)

        # Save combined annotations
        self._save_combined_annotations(num_images, train_ratio, val_ratio)

        # Print statistics
        self._print_statistics()

        return {
            "train": str(self.output_dir / "train_annotations.json"),
            "val": str(self.output_dir / "val_annotations.json"),
            "test": str(self.output_dir / "test_annotations.json"),
        }

    def _get_split(
        self,
        idx: int,
        total: int,
        train_ratio: float,
        val_ratio: float,
    ) -> str:
        """Determine which split an image belongs to."""
        train_end = int(total * train_ratio)
        val_end = int(total * (train_ratio + val_ratio))

        if idx < train_end:
            return "train"
        elif idx < val_end:
            return "val"
        else:
            return "test"

    def _save_combined_annotations(
        self,
        num_images: int,
        train_ratio: float,
        val_ratio: float,
    ):
        """Save combined annotations for each split."""
        train_anns = [a for a in self.annotations if a['split'] == 'train']
        val_anns = [a for a in self.annotations if a['split'] == 'val']
        test_anns = [a for a in self.annotations if a['split'] == 'test']

        with open(self.output_dir / "train_annotations.json", 'w') as f:
            json.dump(train_anns, f, indent=2)

        with open(self.output_dir / "val_annotations.json", 'w') as f:
            json.dump(val_anns, f, indent=2)

        with open(self.output_dir / "test_annotations.json", 'w') as f:
            json.dump(test_anns, f, indent=2)

    def _print_statistics(self):
        """Print dataset statistics."""
        splits = {'train': 0, 'val': 0, 'test': 0}
        conditions = {c: 0 for c in CONDITIONS}

        for ann in self.annotations:
            splits[ann['split']] += 1
            conditions[ann['metadata']['condition']] += 1

        print("\n=== Dataset Statistics ===")
        print(f"Total images: {len(self.annotations)}")
        print(f"  - Train: {splits['train']}")
        print(f"  - Val: {splits['val']}")
        print(f"  - Test: {splits['test']}")
        print("\nCondition distribution:")
        for cond, count in conditions.items():
            print(f"  - {cond}: {count}")


def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(description="Generate mock dataset for logistics extraction")
    parser.add_argument(
        "--num_images",
        type=int,
        default=100,
        help="Number of images to generate (default: 100)"
    )
    parser.add_argument(
        "--output_dir",
        type=str,
        default="data/raw",
        help="Output directory (default: data/raw)"
    )
    parser.add_argument(
        "--train_ratio",
        type=float,
        default=0.7,
        help="Training set ratio (default: 0.7)"
    )
    parser.add_argument(
        "--val_ratio",
        type=float,
        default=0.15,
        help="Validation set ratio (default: 0.15)"
    )

    args = parser.parse_args()

    generator = DatasetGenerator(args.output_dir)
    splits = generator.generate_dataset(
        num_images=args.num_images,
        train_ratio=args.train_ratio,
        val_ratio=args.val_ratio,
    )

    print(f"\nDataset saved to: {args.output_dir}")
    print(f"  Train annotations: {splits['train']}")
    print(f"  Val annotations: {splits['val']}")
    print(f"  Test annotations: {splits['test']}")


if __name__ == "__main__":
    main()
