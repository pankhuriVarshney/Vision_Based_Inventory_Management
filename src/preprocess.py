#!/usr/bin/env python3
"""
Data Preprocessing for Retail Inventory Detection
Supports: COCO- 2017 (fast, auto-download), RPC (retail-specific), or SKU-110K (full only)
"""

import os
import shutil
import urllib.request
import zipfile
import json
from pathlib import Path
import numpy as np
import pandas as pd
from tqdm import tqdm
import cv2
import random
import argparse
from collections import defaultdict
from ultralytics import YOLO  # For COCO auto-download verification
from ultralytics.utils.downloads import download  # Ultralytics download utility

class DatasetPreprocessor:
    def __init__(self, data_dir="./data", dataset_type="coco"):
        """
        Args:
            data_dir: Root directory for data
            dataset_type: 'coco' (fast, auto), 'rpc' (retail), or 'sku110k' (full only)
        """
        self.data_dir = Path(data_dir)
        self.dataset_type = dataset_type.lower()
        self.dataset_dir = self.data_dir / self.dataset_type
        self.images_dir = self.dataset_dir / "images"
        self.labels_dir = self.dataset_dir / "labels"
        
        # Create directories
        self.dataset_dir.mkdir(parents=True, exist_ok=True)
        self.images_dir.mkdir(exist_ok=True)
        self.labels_dir.mkdir(parents=True, exist_ok=True)
        
    def preprocess_coco(self):
        """
        Use COCO-2017 dataset with automatic image download via Ultralytics
        Downloads both images and annotations automatically
        """
        print("Using COCO-2017 Dataset (Auto-download via Ultralytics)")
        print("Download time: ~10-15 minutes (18GB total)")
        print("This will download train2017 (~13GB) and val2017 (~6GB)")
        print("Only retail-relevant classes will be kept for labels\n")
        
        # COCO classes that represent retail products
        self.retail_classes = {
            39: 'bottle', 40: 'wine glass', 41: 'cup', 42: 'fork', 43: 'knife',
            44: 'spoon', 45: 'bowl', 46: 'banana', 47: 'apple', 48: 'sandwich',
            49: 'orange', 50: 'broccoli', 51: 'carrot', 52: 'hot dog', 53: 'pizza',
            54: 'donut', 55: 'cake', 73: 'book', 74: 'clock', 75: 'vase',
            76: 'scissors', 77: 'teddy bear', 78: 'hair drier', 79: 'toothbrush',
            24: 'backpack', 25: 'umbrella', 26: 'handbag', 27: 'tie', 28: 'suitcase',
            32: 'sports ball', 33: 'kite', 34: 'baseball bat', 35: 'baseball glove',
            36: 'skateboard', 37: 'surfboard', 38: 'tennis racket',
            67: 'cell phone', 68: 'microwave', 69: 'oven', 70: 'toaster',
            71: 'sink', 72: 'refrigerator', 63: 'laptop', 64: 'mouse',
            65: 'remote', 66: 'keyboard', 62: 'tv'
        }
        
        print("Selected retail-relevant COCO classes:")
        class_list = [f"{idx}:{name}" for idx, name in self.retail_classes.items()]
        for i in range(0, len(class_list), 4):
            print("   " + "  ".join(class_list[i:i+4]))
        
        # Step 1: Download COCO images and annotations using Ultralytics
        self._download_coco_full()
        
        # Step 2: Convert annotations to YOLO format (retail classes only)
        self._convert_coco_to_yolo()
        
        # Step 3: Create YAML config
        self._create_coco_yaml()
        
        return True
    
    def _download_coco_full(self):
        """
        Download COCO 2017 dataset using Ultralytics' built-in downloader
        This handles images and annotations automatically
        """
        print("\nDownloading COCO 2017 dataset...")
        print("   This uses Ultralytics' automatic downloader")
        print("   Files will be cached in the dataset directory\n")
        
        # Use Ultralytics to download COCO (this handles everything)
        # We'll use the YAML approach to trigger automatic download
        coco_yaml_path = self.dataset_dir / "coco_original.yaml"
        
        # Create temporary YAML for Ultralytics to download COCO
        yaml_content = f"""
# COCO 2017 dataset http://cocodataset.org
path: {self.dataset_dir}  # dataset root dir
train: train2017  # train images (relative to 'path') 118287 images
val: val2017  # val images (relative to 'path') 5000 images

# Classes
names:
  0: person
  1: bicycle
  2: car
  3: motorcycle
  4: airplane
  5: bus
  6: train
  7: truck
  8: boat
  9: traffic light
  10: fire hydrant
  11: stop sign
  12: parking meter
  13: bench
  14: bird
  15: cat
  16: dog
  17: horse
  18: sheep
  19: cow
  20: elephant
  21: bear
  22: zebra
  23: giraffe
  24: backpack
  25: umbrella
  26: handbag
  27: tie
  28: suitcase
  29: frisbee
  30: skis
  31: snowboard
  32: sports ball
  33: kite
  34: baseball bat
  35: baseball glove
  36: skateboard
  37: surfboard
  38: tennis racket
  39: bottle
  40: wine glass
  41: cup
  42: fork
  43: knife
  44: spoon
  45: bowl
  46: banana
  47: apple
  48: sandwich
  49: orange
  50: broccoli
  51: carrot
  52: hot dog
  53: pizza
  54: donut
  55: cake
  56: chair
  57: couch
  58: potted plant
  59: bed
  60: dining table
  61: toilet
  62: tv
  63: laptop
  64: mouse
  65: remote
  66: keyboard
  67: cell phone
  68: microwave
  69: oven
  70: toaster
  71: sink
  72: refrigerator
  73: book
  74: clock
  75: vase
  76: scissors
  77: teddy bear
  78: hair drier
  79: toothbrush

# Download script/URL (optional)
download: |
  from ultralytics.utils.downloads import download
  from pathlib import Path

  # Download labels
  segments = ['train2017', 'val2017']
  dir = Path(self.dataset_dir)
  url = 'https://github.com/ultralytics/assets/releases/download/v0.0.0/'
  urls = [url + 'coco2017labels-segments.zip']  # labels
  download(urls, dir=dir.parent)

  # Download data
  urls = ['http://images.cocodataset.org/zips/train2017.zip', 
          'http://images.cocodataset.org/zips/val2017.zip']
  download(urls, dir=dir / 'images', threads=3)
"""
        
        with open(coco_yaml_path, 'w') as f:
            f.write(yaml_content)
        
        print("   Triggering Ultralytics COCO download...")
        print("   This will download ~18GB of data. Progress will be shown.\n")
        
        try:
            # This triggers the download automatically
            model = YOLO('yolov8n.pt')  # Load a small model just to init
            # Use the dataset to trigger download
            print("    Downloading COCO images and labels...")
            print("    This may take 10-15 minutes depending on your connection...")
            
            # Manual download approach for better control
            self._manual_download_coco()
            
        except Exception as e:
            print(f"    Auto-download note: {e}")
            print("   Attempting manual download...")
            self._manual_download_coco()
    
    def _manual_download_coco(self):
        """Manual download with progress tracking"""
        base_url = "http://images.cocodataset.org/zips/"
        annot_url = "http://images.cocodataset.org/annotations/annotations_trainval2017.zip"
        
        # Download annotations first (smaller)
        annot_zip = self.dataset_dir / "annotations_trainval2017.zip"
        if not (self.dataset_dir / "annotations").exists():
            if not annot_zip.exists():
                print("   Downloading annotations (~250MB)...")
                self._download_with_progress(annot_url, annot_zip)
            
            print("   Extracting annotations...")
            with zipfile.ZipFile(annot_zip, 'r') as z:
                z.extractall(self.dataset_dir)
        
        # Download train images
        train_zip = self.dataset_dir / "train2017.zip"
        train_dir = self.dataset_dir / "train2017"
        if not train_dir.exists():
            if not train_zip.exists():
                print("   Downloading train2017 images (~13GB)...")
                print("    This will take several minutes...")
                self._download_with_progress(base_url + "train2017.zip", train_zip)
            
            print("   Extracting train images...")
            with zipfile.ZipFile(train_zip, 'r') as z:
                z.extractall(self.dataset_dir)
        
        # Download val images
        val_zip = self.dataset_dir / "val2017.zip"
        val_dir = self.dataset_dir / "val2017"
        if not val_dir.exists():
            if not val_zip.exists():
                print("   Downloading val2017 images (~6GB)...")
                self._download_with_progress(base_url + "val2017.zip", val_zip)
            
            print("   Extracting val images...")
            with zipfile.ZipFile(val_zip, 'r') as z:
                z.extractall(self.dataset_dir)
        
        # Move to standard location
        if train_dir.exists():
            shutil.move(str(train_dir), str(self.images_dir / "train"))
        if val_dir.exists():
            shutil.move(str(val_dir), str(self.images_dir / "val"))
        
        print("   COCO download complete!")
    
    def _download_with_progress(self, url, dest_path):
        """Download file with progress bar"""
        class DownloadProgressBar(tqdm):
            def update_to(self, b=1, bsize=1, tsize=None):
                if tsize is not None:
                    self.total = tsize
                self.update(b * bsize - self.n)
        
        with DownloadProgressBar(unit='B', unit_scale=True, miniters=1, desc=dest_path.name) as t:
            urllib.request.urlretrieve(url, dest_path, reporthook=lambda b, bsize, tsize: t.update_to(b, bsize, tsize))
    
    def _convert_coco_to_yolo(self):
        """Convert COCO annotations to YOLO format, keeping only retail classes"""
        print("\ Converting COCO annotations to YOLO format...")
        print("   Filtering for retail-relevant classes only...")
        
        annot_dir = self.dataset_dir / 'annotations'
        
        for split in ['train', 'val']:
            json_file = annot_dir / f'instances_{split}2017.json'
            
            if not json_file.exists():
                print(f"   ⚠️  {json_file} not found, skipping...")
                continue
            
            print(f"\n   Processing {split}2017...")
            
            with open(json_file) as f:
                coco_data = json.load(f)
            
            # Create image id to filename mapping
            images = {img['id']: img for img in coco_data['images']}
            
            # Group annotations by image (only retail classes)
            img_annotations = defaultdict(list)
            retail_ann_count = 0
            
            for ann in coco_data['annotations']:
                if ann['category_id'] in self.retail_classes:
                    img_annotations[ann['image_id']].append(ann)
                    retail_ann_count += 1
            
            print(f"      Found {retail_ann_count} retail product annotations")
            print(f"      In {len(img_annotations)} images")
            
            # Create directories
            (self.labels_dir / split).mkdir(parents=True, exist_ok=True)
            
            # Process each image
            valid_images = []
            skipped_images = 0
            
            for img_id, anns in tqdm(img_annotations.items(), desc=f"      Converting {split}"):
                img_info = images[img_id]
                img_name = img_info['file_name']
                img_w, img_h = img_info['width'], img_info['height']
                
                # Check if image actually exists
                img_path = self.images_dir / split / img_name
                if not img_path.exists():
                    skipped_images += 1
                    continue
                
                valid_images.append(f"./images/{split}/{img_name}")
                
                # Write YOLO labels
                label_name = Path(img_name).stem + '.txt'
                label_path = self.labels_dir / split / label_name
                
                with open(label_path, 'w') as f:
                    for ann in anns:
                        # COCO bbox is [x, y, width, height]
                        x, y, w, h = ann['bbox']
                        
                        # Skip invalid boxes
                        if w <= 0 or h <= 0:
                            continue
                        
                        # Convert to YOLO format [class, x_center, y_center, width, height]
                        x_center = (x + w/2) / img_w
                        y_center = (y + h/2) / img_h
                        w_norm = w / img_w
                        h_norm = h / img_h
                        
                        # Clamp values to [0, 1]
                        x_center = max(0, min(1, x_center))
                        y_center = max(0, min(1, y_center))
                        w_norm = max(0, min(1, w_norm))
                        h_norm = max(0, min(1, h_norm))
                        
                        f.write(f"0 {x_center:.6f} {y_center:.6f} {w_norm:.6f} {h_norm:.6f}\n")
            
            # Write image list file (only images that exist)
            img_list_file = self.dataset_dir / f'{split}.txt'
            with open(img_list_file, 'w') as f:
                f.write('\n'.join(valid_images))
            
            print(f"       {split}: {len(valid_images)} images with labels")
            if skipped_images > 0:
                print(f"        Skipped {skipped_images} images (not downloaded)")
    
    def _create_coco_yaml(self):
        """Create dataset YAML for YOLO training"""
        yaml_content = f"""# COCO Retail Subset for Inventory Management
path: {self.dataset_dir.absolute()}  # dataset root dir
train: train.txt  # train images list
val: val.txt      # val images list

# Classes (single class for inventory counting)
names:
  0: product

# Retail-relevant COCO classes mapped to single product class
# Original COCO IDs: {sorted(self.retail_classes.keys())}
# Classes: {list(self.retail_classes.values())}
"""
        yaml_path = self.dataset_dir / 'dataset.yaml'
        with open(yaml_path, 'w') as f:
            f.write(yaml_content.strip())
        
        print(f"\n    Created dataset config: {yaml_path}")
    
    def preprocess_rpc(self):
        """
        Retail Product Checkout Dataset from Kaggle
        Requires kaggle API: pip install kaggle
        """
        print(" Using RPC (Retail Product Checkout) Dataset")
        print("    30,000 checkout images with 200 product categories")
        print("     Download time: ~10 minutes (1.5GB)")
        print("     Requires Kaggle API credentials")
        print("\n    To set up Kaggle API:")
        print("      1. Go to https://www.kaggle.com/account")
        print("      2. Click 'Create New API Token'")
        print("      3. Save kaggle.json to ~/.kaggle/ (Linux/Mac) or %%USERPROFILE%%\\.kaggle\\ (Windows)")
        print("      4. Run: pip install kaggle")
        
        # Check if kaggle is installed
        try:
            import kaggle
            from kaggle.api.kaggle_api_extended import KaggleApi
        except ImportError:
            print("\n Kaggle API not installed.")
            print("   Run: pip install kaggle")
            return False
        
        # Authenticate first
        print("\ Authenticating with Kaggle...")
        try:
            api = KaggleApi()
            api.authenticate()
            print("    Authentication successful")
        except Exception as e:
            print(f"    Authentication failed: {e}")
            print("   Make sure kaggle.json is in the correct location")
            self._rpc_manual_download_instructions()
            return False
        
        # Download dataset
        print("\n Downloading from Kaggle...")
        print("    This may take 10-15 minutes. Progress will update every 30 seconds...")
        print("   Dataset: diyer22/retail-product-checkout-dataset")
        
        try:
            # Download with progress
            import time
            import threading
            
            download_complete = False
            download_error = None
            
            def download_worker():
                nonlocal download_complete, download_error
                try:
                    # Use quiet=False to show progress, but capture output
                    api.dataset_download_files(
                        'diyer22/retail-product-checkout-dataset',
                        path=self.dataset_dir,
                        unzip=True,
                        quiet=False  # This shows progress in console
                    )
                    download_complete = True
                except Exception as e:
                    download_error = e
                    download_complete = True
            
            # Start download in thread so we can show custom progress
            thread = threading.Thread(target=download_worker)
            thread.start()
            
            # Show spinner while downloading
            spinner = ['⏳ Downloading...', 'Downloading..', ' Downloading.', 'Downloading']
            i = 0
            while not download_complete:
                print(f"\r   {spinner[i % len(spinner)]} (this may take 10+ minutes)", end='', flush=True)
                time.sleep(0.5)
                i += 1
            
            thread.join()
            
            if download_error:
                raise download_error
            
            print("\r    Download complete!                    ")
            
        except Exception as e:
            print(f"\n    Download failed: {e}")
            self._rpc_manual_download_instructions()
            return False
        
        # Organize into YOLO format
        self._organize_rpc()
        return True
    
    def _rpc_manual_download_instructions(self):
        """Show manual download instructions when API fails"""
        print("\n" + "="*60)
        print("MANUAL DOWNLOAD ALTERNATIVE")
        print("="*60)
        print("Since automatic download failed, please download manually:")
        print("\n1. Visit: https://www.kaggle.com/datasets/diyer22/retail-product-checkout-dataset")
        print("2. Click 'Download' (1.5GB zip file)")
        print(f"3. Extract the zip to: {self.dataset_dir}/")
        print("4. Re-run this script - it will organize the files automatically")
        print("="*60 + "\n")
    
    def _organize_rpc(self):
        """Organize RPC dataset into YOLO format"""
        print("\n Organizing RPC dataset...")
        
        # RPC has this structure: train2019/, val2019/, test2019/ with images
        # And annotations in JSON format
        
        # Find all images recursively
        print("   Scanning for images...")
        image_files = []
        for ext in ['*.jpg', '*.jpeg', '*.png']:
            image_files.extend(list(self.dataset_dir.rglob(ext)))
        
        print(f"   Found {len(image_files)} images")
        
        if len(image_files) == 0:
            print("    No images found! Dataset structure may be different.")
            print(f"   Check: {self.dataset_dir}")
            return False
        
        # RPC uses train2019/val2019/test2019 structure
        # Group by directory name
        train_files = [f for f in image_files if 'train' in str(f).lower()]
        val_files = [f for f in image_files if 'val' in str(f).lower()]
        test_files = [f for f in image_files if 'test' in str(f).lower()]
        
        # If no standard split found, do random split
        if not train_files and not val_files:
            print("   No standard train/val split found, using random 80/20 split...")
            random.seed(42)
            random.shuffle(image_files)
            split_idx = int(len(image_files) * 0.8)
            train_files = image_files[:split_idx]
            val_files = image_files[split_idx:]
        
        splits = {'train': train_files, 'val': val_files}
        if test_files:
            splits['test'] = test_files
        
        total_processed = 0
        
        for split, files in splits.items():
            if not files:
                continue
                
            print(f"\n   Processing {split}: {len(files)} images...")
            
            (self.images_dir / split).mkdir(parents=True, exist_ok=True)
            (self.labels_dir / split).mkdir(parents=True, exist_ok=True)
            
            img_list = []
            
            for img_path in tqdm(files, desc=f"   Copying {split}", ncols=70):
                try:
                    # Copy image with simpler naming to avoid conflicts
                    new_name = f"{split}_{img_path.stem}{img_path.suffix}"
                    dest_img = self.images_dir / split / new_name
                    
                    # Copy if not exists
                    if not dest_img.exists():
                        shutil.copy2(img_path, dest_img)
                    
                    img_list.append(f"./images/{split}/{new_name}")
                    
                    # Create empty label (YOLO needs label file even if empty)
                    label_path = self.labels_dir / split / f"{new_name}.txt"
                    if not label_path.exists():
                        label_path.touch()
                    
                    total_processed += 1
                    
                except Exception as e:
                    print(f"     Error with {img_path}: {e}")
                    continue
            
            # Write image list
            list_file = self.dataset_dir / f'{split}.txt'
            with open(list_file, 'w') as f:
                f.write('\n'.join(img_list))
            
            print(f"    {split}: {len(img_list)} images ready")
        
        # Create YAML
        yaml_content = f"""# RPC (Retail Product Checkout) Dataset
path: {self.dataset_dir.absolute()}  # dataset root dir
train: train.txt  # train images
val: val.txt      # val images

# Classes (single class for inventory counting)
names:
  0: product

# Note: RPC has 200 fine-grained categories mapped to single 'product' class
# Original categories include various retail items at checkout counters
"""
        yaml_path = self.dataset_dir / 'dataset.yaml'
        with open(yaml_path, 'w') as f:
            f.write(yaml_content)
        
        print(f"\n    Dataset config: {yaml_path}")
        print(f"\n RPC dataset ready with {total_processed} images!")
        print("   Note: Labels are placeholder. For training with real annotations,")
        print("   parse RPC's JSON annotations to YOLO format.")
        
        return True
    
    def preprocess_sku110k_full(self):
        """Full SKU-110K download (13GB, 10+ hours)"""
        print(" SKU-110K Full Dataset (13GB)")
        print("     This will take 10+ hours!")
        print("    Consider using --dataset coco for immediate testing\n")
        
        url = "http://trax-geometry.s3.amazonaws.com/cvpr_challenge/SKU110K_fixed.tar.gz "
        tar_path = self.data_dir / "SKU110K_fixed.tar.gz"
        
        if not tar_path.exists():
            print(" Downloading...")
            with tqdm(unit='B', unit_scale=True, desc="SKU-110K") as t:
                urllib.request.urlretrieve(url, tar_path, 
                    reporthook=lambda b, bsize, tsize: t.update(bsize) if tsize else t.update(bsize))
        
        print(" Extracting...")
        import tarfile
        with tarfile.open(tar_path, 'r:gz') as tar:
            tar.extractall(self.data_dir)
        
        if (self.data_dir / "SKU110K_fixed").exists():
            shutil.move(self.data_dir / "SKU110K_fixed", self.dataset_dir)
        
        # Convert annotations (simplified)
        self._convert_sku_annotations()
        return True
    
    def _convert_sku_annotations(self):
        """Convert SKU-110K CSV to YOLO"""
        annot_dir = self.dataset_dir / 'annotations'
        if not annot_dir.exists():
            print(" No annotations found")
            return
        
        for split in ['train', 'val', 'test']:
            csv_file = annot_dir / f'annotations_{split}.csv'
            if not csv_file.exists():
                continue
            
            df = pd.read_csv(csv_file, header=None,
                           names=['image', 'x1', 'y1', 'x2', 'y2', 'class', 'width', 'height'])
            
            grouped = df.groupby('image')
            
            with open(self.dataset_dir / f'{split}.txt', 'w') as f:
                for img_name in tqdm(grouped.groups.keys(), desc=f"Converting {split}"):
                    f.write(f"./images/{img_name}\n")
                    
                    img_data = grouped.get_group(img_name)
                    label_file = self.labels_dir / f"{Path(img_name).stem}.txt"
                    
                    with open(label_file, 'w') as lf:
                        for _, row in img_data.iterrows():
                            w, h = row['width'], row['height']
                            x_center = (row['x1'] + row['x2']) / 2 / w
                            y_center = (row['y1'] + row['y2']) / 2 / h
                            width = (row['x2'] - row['x1']) / w
                            height = (row['y2'] - row['y1']) / h
                            lf.write(f"0 {x_center:.6f} {y_center:.6f} {width:.6f} {height:.6f}\n")
    
    def verify(self):
        """Verify dataset"""
        print(f"\n Verifying {self.dataset_type} dataset...")
        
        for split in ['train', 'val']:
            list_file = self.dataset_dir / f'{split}.txt'
            if list_file.exists():
                content = list_file.read_text().strip()
                imgs = [l.strip() for l in content.split('\n') if l.strip()] if content else []
                
                # Count actual existing images
                existing = sum(1 for img in imgs if (self.dataset_dir / img).exists())
                print(f"   {split}: {len(imgs)} entries, {existing} images exist")
        
        labels = list(self.labels_dir.rglob('*.txt'))
        print(f"   Labels: {len(labels)} files")
        
        yaml_file = self.dataset_dir / 'dataset.yaml'
        if yaml_file.exists():
            print(f"    Config: {yaml_file}")

def main():
    parser = argparse.ArgumentParser(description='Retail Inventory Dataset Preprocessor')
    parser.add_argument('--dataset', choices=['coco', 'rpc', 'sku110k'], default='coco',
                       help='Dataset to use: coco (fast, auto), rpc (retail-specific), sku110k (slow)')
    parser.add_argument('--data-dir', default='./data', help='Data directory')
    
    args = parser.parse_args()
    
    preprocessor = DatasetPreprocessor(
        data_dir=args.data_dir,
        dataset_type=args.dataset
    )
    
    # Process based on dataset type
    if args.dataset == 'coco':
        success = preprocessor.preprocess_coco()
    elif args.dataset == 'rpc':
        success = preprocessor.preprocess_rpc()
    else:
        success = preprocessor.preprocess_sku110k_full()
    
    if success:
        preprocessor.verify()
        print(f"\n {args.dataset.upper()} dataset ready!")
        print(f"   Train: python src/train.py --data {preprocessor.dataset_dir}/dataset.yaml")
    else:
        print(f"\n❌ Failed to prepare {args.dataset} dataset")

if __name__ == "__main__":
    main()