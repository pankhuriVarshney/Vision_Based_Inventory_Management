#!/usr/bin/env python3
"""
TRAINING - FIXED for actual directory structure
Images: data/rpc/train2019/ and data/rpc/val2019/
Labels: data/rpc/labels/train/ and data/rpc/labels/val/
"""

import os
import random
import shutil
from pathlib import Path
from ultralytics import YOLO
import argparse

def create_mini_dataset_with_labels(source_dir="data/rpc", num_images=500):
    """
    Create mini dataset from actual RPC structure
    """
    source_dir = Path(source_dir)
    mini_dir = Path("data/rpc_mini_real")
    
    print(f" Creating MINI dataset with {num_images} images + REAL labels...")
    
    # Create structure
    (mini_dir / "images/train").mkdir(parents=True, exist_ok=True)
    (mini_dir / "labels/train").mkdir(parents=True, exist_ok=True)
    (mini_dir / "images/val").mkdir(parents=True, exist_ok=True)
    (mini_dir / "labels/val").mkdir(parents=True, exist_ok=True)
    
    # Map actual directory structure
    # Images: train2019/, val2019/
    # Labels: labels/train/, labels/val/
    split_map = {
        'train': {'img_dir': source_dir / 'train2019', 'label_dir': source_dir / 'labels' / 'train'},
        'val': {'img_dir': source_dir / 'val2019', 'label_dir': source_dir / 'labels' / 'val'}
    }
    
    # Collect all images with labels
    all_images = []
    for split_name, paths in split_map.items():
        img_dir = paths['img_dir']
        label_dir = paths['label_dir']
        
        if not img_dir.exists():
            print(f"     Image dir not found: {img_dir}")
            continue
        if not label_dir.exists():
            print(f"    Label dir not found: {label_dir}")
            continue
            
        print(f"   Checking {split_name}: {img_dir}")
        
        # Find all images and check for labels
        for ext in ['*.jpg', '*.png', '*.jpeg']:
            for img_path in img_dir.glob(ext):
                label_path = label_dir / f"{img_path.stem}.txt"
                if label_path.exists() and label_path.stat().st_size > 0:
                    all_images.append((img_path, label_path, split_name))
                elif label_path.exists():
                    # Empty label file exists but skip it
                    pass
                else:
                    # No label file
                    pass
    
    if len(all_images) == 0:
        print(" No images with labels found!")
        print(f"   Searched in:")
        for split_name, paths in split_map.items():
            print(f"      Images: {paths['img_dir']} (exists: {paths['img_dir'].exists()})")
            print(f"      Labels: {paths['label_dir']} (exists: {paths['label_dir'].exists()})")
        return None
    
    print(f"   Found {len(all_images)} images with labels")
    
    # Random sample
    random.seed(42)
    selected = random.sample(all_images, min(num_images, len(all_images)))
    
    # Split 80/20 for train/val (regardless of original split)
    split_idx = int(len(selected) * 0.8)
    train_items = selected[:split_idx]
    val_items = selected[split_idx:]
    
    def copy_with_labels(items, split_name):
        """Copy images AND labels"""
        img_list = []
        labels_copied = 0
        
        for img_path, label_path, orig_split in items:
            # Use original filename
            dest_img = mini_dir / f"images/{split_name}" / img_path.name
            dest_label = mini_dir / f"labels/{split_name}" / f"{img_path.stem}.txt"
            
            # Copy image
            shutil.copy2(img_path, dest_img)
            img_list.append(f"./images/{split_name}/{img_path.name}")
            
            # Copy label
            shutil.copy2(label_path, dest_label)
            labels_copied += 1
        
        # Write image list
        list_file = mini_dir / f"{split_name}.txt"
        with open(list_file, 'w') as f:
            f.write('\n'.join(img_list))
        
        return len(items), labels_copied
    
    print(f"\nProcessing train split...")
    train_count, train_labels = copy_with_labels(train_items, "train")
    
    print(f"Processing val split...")
    val_count, val_labels = copy_with_labels(val_items, "val")
    
    # Create YAML
    yaml_content = f"""path: {mini_dir.absolute()}
train: train.txt
val: val.txt
names:
  0: product
nc: 1
"""
    yaml_path = mini_dir / "dataset.yaml"
    with open(yaml_path, 'w') as f:
        f.write(yaml_content)
    
    print(f"\n{'='*60}")
    print(f" Mini dataset created!")
    print(f"{'='*60}")
    print(f"   Train: {train_count} images ({train_labels} with labels)")
    print(f"   Val: {val_count} images ({val_labels} with labels)")
    print(f"   Config: {yaml_path}")
    
    if train_labels == 0:
        print(f"\n  WARNING: No labels found!")
        return None
    
    return yaml_path

def train_with_real_labels(data_yaml, epochs=20, imgsz=640):
    """Train with real labels"""
    print(f"\n{'='*60}")
    print(f"TRAINING WITH REAL LABELS")
    print(f"{'='*60}")
    print(f"   Data: {data_yaml}")
    print(f"   Epochs: {epochs}")
    print(f"   Image size: {imgsz}")
    
    # Verify labels exist
    mini_dir = Path("data/rpc_mini_real")
    train_labels = list((mini_dir / "labels/train").glob("*.txt"))
    non_empty = sum(1 for f in train_labels if f.stat().st_size > 0)
    
    print(f"   Labels: {non_empty}/{len(train_labels)} files have annotations")
    
    if non_empty == 0:
        print(f"\n ERROR: No labels found! Cannot train.")
        return None, None
    
    model = YOLO("yolov8n.pt")
    
    args = {
        'data': str(data_yaml),
        'epochs': epochs,
        'batch': 8,
        'imgsz': imgsz,
        'device': 'cpu',
        'workers': 4,
        'cache': False,
        'single_cls': True,
        'hsv_h': 0.015,
        'hsv_s': 0.7,
        'hsv_v': 0.4,
        'degrees': 0.0,
        'translate': 0.1,
        'scale': 0.5,
        'shear': 0.0,
        'perspective': 0.0,
        'flipud': 0.0,
        'fliplr': 0.5,
        'mosaic': 1.0,
        'mixup': 0.0,
        'warmup_epochs': 3,
        'patience': 10,
        'save': True,
        'project': 'models',
        'name': 'rpc_real_labels',
        'exist_ok': True,
        'verbose': True,
    }
    
    print(f"\n⏳ Starting training...")
    results = model.train(**args)
    return model, results

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument('--images', type=int, default=500)
    parser.add_argument('--epochs', type=int, default=20)
    parser.add_argument('--imgsz', type=int, default=640)
    args = parser.parse_args()
    
    mini_yaml = create_mini_dataset_with_labels(num_images=args.images)
    
    if mini_yaml and Path(mini_yaml).exists():
        model, results = train_with_real_labels(mini_yaml, epochs=args.epochs, imgsz=args.imgsz)
        
        if model:
            print(f"\n{'='*60}")
            print(f" TRAINING COMPLETE!")
            print(f"{'='*60}")
            print(f"   Model: models/rpc_real_labels/weights/best.pt")
    else:
        print(f" Failed to create dataset")