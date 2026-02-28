#!/usr/bin/env python3
"""
EMERGENCY FIX - Finds images wherever they are
"""

import json
from pathlib import Path
from collections import defaultdict
import shutil

def convert_rpc_to_yolo():
    rpc_dir = Path("data/rpc")
    
    # Process train and val
    for split in ['train', 'val']:
        json_file = rpc_dir / f"instances_{split}2019.json"
        
        if not json_file.exists():
            print(f" {json_file} not found")
            continue
        
        print(f"\n{'='*60}")
        print(f" Processing {json_file.name}...")
        
        with open(json_file) as f:
            data = json.load(f)
        
        images = {img['id']: img for img in data['images']}
        print(f"   JSON has {len(images)} images")
        
        # Group annotations
        img_annotations = defaultdict(list)
        for ann in data['annotations']:
            img_annotations[ann['image_id']].append(ann)
        
        # Create label dir
        label_dir = rpc_dir / "labels" / split
        label_dir.mkdir(parents=True, exist_ok=True)
        
        # Find all images recursively (search everywhere in data/rpc/)
        print(f"   Scanning for images...")
        all_image_files = {}
        for ext in ['*.jpg', '*.png', '*.jpeg']:
            for img_path in rpc_dir.rglob(ext):
                all_image_files[img_path.name] = img_path
                all_image_files[img_path.stem] = img_path  # Also map by stem
        
        print(f"   Found {len(all_image_files)} image files total")
        
        # Convert
        converted = 0
        for img_id, anns in img_annotations.items():
            img_info = images.get(img_id)
            if not img_info:
                continue
            
            img_name = img_info['file_name']
            img_w = img_info['width']
            img_h = img_info['height']
            
            # Try to find image by various names
            possible_keys = [
                img_name,
                img_name.replace('.jpg', '.png'),
                img_name.replace('.png', '.jpg'),
                Path(img_name).stem,
                f"{split}_{img_name}",
                f"{split}2019_{img_name}"
            ]
            
            img_path = None
            for key in possible_keys:
                if key in all_image_files:
                    img_path = all_image_files[key]
                    break
            
            if not img_path:
                continue  # Skip if image not found
            
            # Create label
            label_name = Path(img_name).stem + '.txt'
            label_path = label_dir / label_name
            
            with open(label_path, 'w') as f:
                for ann in anns:
                    x, y, bw, bh = ann['bbox']
                    if bw <= 0 or bh <= 0:
                        continue
                    
                    x_center = (x + bw/2) / img_w
                    y_center = (y + bh/2) / img_h
                    nw = bw / img_w
                    nh = bh / img_h
                    
                    x_center = max(0, min(1, x_center))
                    y_center = max(0, min(1, y_center))
                    nw = max(0, min(1, nw))
                    nh = max(0, min(1, nh))
                    
                    f.write(f"0 {x_center:.6f} {y_center:.6f} {nw:.6f} {nh:.6f}\n")
            
            converted += 1
        
        print(f"   Created: {converted} label files")
    
    print(f"\n{'='*60}")
    print(f" Done! Check data/rpc/labels/")
    print(f"{'='*60}")

if __name__ == "__main__":
    convert_rpc_to_yolo()