#!/usr/bin/env python3
"""
Enhanced Training Script with Proper Class Names
"""

import os
import yaml
from pathlib import Path
from ultralytics import YOLO
import argparse

# Class mapping for RPC dataset (common retail products)
CLASS_NAMES = {
    0: 'chips_snacks',
    1: 'chocolate',
    2: 'candy',
    3: 'desserts',
    4: 'soft_drink',
    5: 'juice',
    6: 'milk_dairy',
    7: 'dried_food',
    8: 'canned_food',
    9: 'seasoning',
    10: 'tissue_paper',
    11: 'stationary'
}

def create_dataset_yaml_with_names(data_dir: str = None, output_file: str = None):
    """Create dataset YAML with proper class names"""
    
    # Find the correct data directory
    if data_dir is None:
        # Try multiple possible paths
        possible_paths = [
            Path("C:/Users/pankh/Documents/Vision_Based_Inventory_Management/data/rpc_mini_real"),
            Path("../data/rpc_mini_real"),
            Path("data/rpc_mini_real"),
            Path("./data/rpc_mini_real"),
        ]
        
        for path in possible_paths:
            if path.exists():
                data_dir = str(path)
                print(f"✅ Found data directory: {data_dir}")
                break
    
    if data_dir is None:
        print(f"❌ Data directory not found!")
        print(f"   Looking in: {possible_paths}")
        return None
    
    data_path = Path(data_dir)
    if not data_path.exists():
        print(f"❌ Data directory not found: {data_dir}")
        return None
    
    # Check if train.txt and val.txt exist, if not create them
    train_txt = data_path / "train.txt"
    val_txt = data_path / "val.txt"
    
    if not train_txt.exists() or not val_txt.exists():
        print(f"📝 Creating train.txt and val.txt files...")
        
        # Create train.txt with all images in train folder
        train_img_dir = data_path / "images/train"
        if train_img_dir.exists():
            with open(train_txt, 'w') as f:
                for img_path in train_img_dir.glob("*.jpg"):
                    f.write(f"./images/train/{img_path.name}\n")
                for img_path in train_img_dir.glob("*.png"):
                    f.write(f"./images/train/{img_path.name}\n")
            print(f"   Created train.txt with {len(list(train_img_dir.glob('*')))} images")
        
        # Create val.txt with all images in val folder
        val_img_dir = data_path / "images/val"
        if val_img_dir.exists():
            with open(val_txt, 'w') as f:
                for img_path in val_img_dir.glob("*.jpg"):
                    f.write(f"./images/val/{img_path.name}\n")
                for img_path in val_img_dir.glob("*.png"):
                    f.write(f"./images/val/{img_path.name}\n")
            print(f"   Created val.txt with {len(list(val_img_dir.glob('*')))} images")
    
    yaml_content = {
        'path': str(data_path.absolute()),
        'train': 'train.txt',
        'val': 'val.txt',
        'nc': len(CLASS_NAMES),
        'names': CLASS_NAMES
    }
    
    if output_file is None:
        output_file = data_path / "dataset_with_names.yaml"
    
    with open(output_file, 'w') as f:
        yaml.dump(yaml_content, f, default_flow_style=False)
    
    print(f"\n✅ Created dataset config: {output_file}")
    print(f"   Classes: {len(CLASS_NAMES)} categories")
    for idx, name in list(CLASS_NAMES.items())[:5]:  # Show first 5
        print(f"      {idx}: {name}")
    print(f"      ... and {len(CLASS_NAMES) - 5} more")
    
    return output_file

def train_with_class_names(data_yaml, epochs=30, imgsz=640, batch=8):
    """Train YOLO with proper class names"""
    
    print(f"\n{'='*60}")
    print(f"🚀 Training YOLOv8n with Class Names")
    print(f"{'='*60}")
    print(f"   Data: {data_yaml}")
    print(f"   Epochs: {epochs}")
    print(f"   Image Size: {imgsz}")
    print(f"   Batch: {batch}")
    
    # Load pretrained model
    model = YOLO("yolov8n.pt")
    
    # Training arguments
    results = model.train(
        data=str(data_yaml),
        epochs=epochs,
        batch=batch,
        imgsz=imgsz,
        device='cpu',  # Use 'cuda' if you have GPU
        workers=4,
        patience=10,
        save=True,
        project='models',
        name='rpc_with_names',
        exist_ok=True,
        pretrained=True,
        optimizer='AdamW',
        lr0=0.001,
        lrf=0.01,
        momentum=0.937,
        weight_decay=0.0005,
        warmup_epochs=3,
        warmup_momentum=0.8,
        warmup_bias_lr=0.1,
        box=7.5,
        cls=0.5,
        dfl=1.5,
        hsv_h=0.015,
        hsv_s=0.7,
        hsv_v=0.4,
        degrees=0.0,
        translate=0.1,
        scale=0.5,
        shear=0.0,
        perspective=0.0,
        flipud=0.0,
        fliplr=0.5,
        mosaic=1.0,
        mixup=0.0,
        copy_paste=0.0
    )
    
    print(f"\n✅ Training complete!")
    print(f"   Model saved to: models/rpc_with_names/weights/best.pt")
    
    return model, results

def validate_model(model_path: str):
    """Validate model performance"""
    print(f"\n{'='*60}")
    print(f"🔍 Validating Model")
    print(f"{'='*60}")
    
    model = YOLO(model_path)
    metrics = model.val()
    
    print(f"\n📊 Validation Results:")
    print(f"   mAP@0.5: {metrics.box.map50:.3f}")
    print(f"   mAP@0.5:0.95: {metrics.box.map:.3f}")
    print(f"   Precision: {metrics.box.mp:.3f}")
    print(f"   Recall: {metrics.box.mr:.3f}")
    
    return metrics

def check_dataset_structure():
    """Check and report dataset structure"""
    print("\n" + "="*60)
    print("📁 Checking Dataset Structure")
    print("="*60)
    
    base_path = Path("C:/Users/pankh/Documents/Vision_Based_Inventory_Management/data/rpc_mini_real")
    
    if not base_path.exists():
        print(f"❌ Dataset not found at: {base_path}")
        return False
    
    print(f"✅ Dataset found at: {base_path}")
    
    # Check directories
    train_images = base_path / "images/train"
    val_images = base_path / "images/val"
    train_labels = base_path / "labels/train"
    val_labels = base_path / "labels/val"
    
    if train_images.exists():
        num_train = len(list(train_images.glob("*")))
        print(f"   Train images: {num_train}")
    else:
        print(f"   ❌ Train images missing")
        return False
    
    if val_images.exists():
        num_val = len(list(val_images.glob("*")))
        print(f"   Val images: {num_val}")
    else:
        print(f"   ❌ Val images missing")
        return False
    
    if train_labels.exists():
        num_train_labels = len(list(train_labels.glob("*.txt")))
        print(f"   Train labels: {num_train_labels}")
    else:
        print(f"   ⚠️ Train labels directory missing")
    
    if val_labels.exists():
        num_val_labels = len(list(val_labels.glob("*.txt")))
        print(f"   Val labels: {num_val_labels}")
    else:
        print(f"   ⚠️ Val labels directory missing")
    
    return True

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument('--data', type=str, default=None, help='Path to dataset')
    parser.add_argument('--epochs', type=int, default=30)
    parser.add_argument('--imgsz', type=int, default=640)
    parser.add_argument('--batch', type=int, default=8)
    parser.add_argument('--check', action='store_true', help='Just check dataset structure')
    args = parser.parse_args()
    
    if args.check:
        check_dataset_structure()
    else:
        # First check dataset structure
        if not check_dataset_structure():
            print("\n❌ Dataset check failed. Please fix paths and try again.")
            exit(1)
        
        # Create dataset config
        yaml_path = create_dataset_yaml_with_names(args.data)
        
        if yaml_path and Path(yaml_path).exists():
            # Train model
            model, results = train_with_class_names(yaml_path, args.epochs, args.imgsz, args.batch)
            
            # Validate
            if model:
                model_path = Path("models/rpc_with_names/weights/best.pt")
                if model_path.exists():
                    validate_model(str(model_path))
                else:
                    print(f"\n⚠️ Model not found at {model_path}")
        else:
            print(f"\n❌ Failed to create dataset YAML")