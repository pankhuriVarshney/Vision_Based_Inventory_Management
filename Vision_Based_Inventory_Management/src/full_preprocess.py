#!/usr/bin/env python3
"""
Data Preprocessing for Retail Inventory Detection
Handles SKU-110K dataset download and format conversion
"""

import os
import shutil
import urllib.request
import tarfile
from pathlib import Path
import numpy as np
import pandas as pd
from tqdm import tqdm
import cv2
from ultralytics.utils.ops import xyxy2xywh

class SKU110KPreprocessor:
    def __init__(self, data_dir="./data"):
        self.data_dir = Path(data_dir)
        self.sku_dir = self.data_dir / "SKU-110K"
        self.images_dir = self.sku_dir / "images"
        self.labels_dir = self.sku_dir / "labels"
        self.annotations_dir = self.sku_dir / "annotations"
        
    def download_dataset(self):
        """Download SKU-110K dataset"""
        print("📥 Downloading SKU-110K dataset...")
        url = "http://trax-geometry.s3.amazonaws.com/cvpr_challenge/SKU110K_fixed.tar.gz"
        tar_path = self.data_dir / "SKU110K_fixed.tar.gz"
        
        if not tar_path.exists():
            # Download with progress bar
            class DownloadProgressBar(tqdm):
                def update_to(self, b=1, bsize=1, tsize=None):
                    if tsize is not None:
                        self.total = tsize
                    self.update(b * bsize - self.n)
            
            with DownloadProgressBar(unit='B', unit_scale=True, miniters=1, desc="SKU-110K") as t:
                urllib.request.urlretrieve(url, tar_path, reporthook=t.update_to)
        
        # Extract
        print("📦 Extracting dataset...")
        with tarfile.open(tar_path, 'r:gz') as tar:
            tar.extractall(self.data_dir)
        
        # Rename directory
        extracted_dir = self.data_dir / "SKU110K_fixed"
        if extracted_dir.exists():
            shutil.move(extracted_dir, self.sku_dir)
        
        print(f"✅ Dataset ready at {self.sku_dir}")
        return self.sku_dir
    
    def convert_annotations(self):
        """Convert CSV annotations to YOLO format"""
        print("🔄 Converting annotations to YOLO format...")
        
        self.labels_dir.mkdir(parents=True, exist_ok=True)
        
        # Process train, val, test
        splits = ['train', 'val', 'test']
        
        for split in splits:
            csv_file = self.annotations_dir / f"annotations_{split}.csv"
            if not csv_file.exists():
                print(f"⚠️  {csv_file} not found, skipping...")
                continue
            
            # Read CSV
            df = pd.read_csv(csv_file, header=None, 
                           names=['image', 'x1', 'y1', 'x2', 'y2', 'class', 'width', 'height'])
            
            # Group by image
            grouped = df.groupby('image')
            
            # Create image list file
            img_list_file = self.sku_dir / f"{split}.txt"
            with open(img_list_file, 'w') as f:
                for img_name in tqdm(grouped.groups.keys(), desc=f"Processing {split}"):
                    f.write(f"./images/{img_name}\n")
                    
                    # Get annotations for this image
                    img_data = grouped.get_group(img_name)
                    
                    # Create YOLO label file
                    label_file = self.labels_dir / f"{Path(img_name).stem}.txt"
                    
                    with open(label_file, 'w') as lf:
                        for _, row in img_data.iterrows():
                            # Normalize coordinates
                            w, h = row['width'], row['height']
                            x_center = (row['x1'] + row['x2']) / 2 / w
                            y_center = (row['y1'] + row['y2']) / 2 / h
                            width = (row['x2'] - row['x1']) / w
                            height = (row['y2'] - row['y1']) / h
                            
                            # Class 0 for single-class detection
                            lf.write(f"0 {x_center:.6f} {y_center:.6f} {width:.6f} {height:.6f}\n")
        
        print("✅ Annotation conversion complete!")
    
    def verify_dataset(self):
        """Verify dataset integrity"""
        print("🔍 Verifying dataset...")
        
        train_imgs = list((self.sku_dir / "train.txt").read_text().strip().split('\n')) if (self.sku_dir / "train.txt").exists() else []
        val_imgs = list((self.sku_dir / "val.txt").read_text().strip().split('\n')) if (self.sku_dir / "val.txt").exists() else []
        
        print(f"   Train images: {len(train_imgs)}")
        print(f"   Val images: {len(val_imgs)}")
        print(f"   Label files: {len(list(self.labels_dir.glob('*.txt')))}")
        
        # Check a sample
        if train_imgs:
            sample_img = self.sku_dir / train_imgs[0].strip('./')
            sample_lbl = self.labels_dir / f"{sample_img.stem}.txt"
            print(f"   Sample: {sample_img.name} -> {sample_lbl.exists()}")

def main():
    preprocessor = SKU110KPreprocessor()
    
    # Download if not exists
    if not preprocessor.sku_dir.exists():
        preprocessor.download_dataset()
    
    # Convert annotations
    preprocessor.convert_annotations()
    
    # Verify
    preprocessor.verify_dataset()
    
    print("\n🎉 Preprocessing complete! Ready for training.")

if __name__ == "__main__":
    main()