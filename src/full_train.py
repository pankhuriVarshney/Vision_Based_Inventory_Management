#!/usr/bin/env python3
"""
YOLOv8 Training Script for Retail Inventory Detection
OPTIMIZED FOR CPU - 32 CORES
"""

import os
import torch
import multiprocessing as mp
from pathlib import Path
from ultralytics import YOLO

# CRITICAL: Set multiprocessing start method BEFORE anything else
# This prevents deadlocks with 32 cores
try:
    mp.set_start_method('spawn', force=True)
except RuntimeError:
    pass

# Environment variables for maximum CPU performance
os.environ['OMP_NUM_THREADS'] = '32'
os.environ['MKL_NUM_THREADS'] = '32'
os.environ['OPENBLAS_NUM_THREADS'] = '32'
os.environ['VECLIB_MAXIMUM_THREADS'] = '32'
os.environ['NUMEXPR_NUM_THREADS'] = '32'
os.environ['KMP_AFFINITY'] = 'granularity=fine,compact,1,0'
os.environ['KMP_BLOCKTIME'] = '0'

def train_model_cpu(
    data_yaml="data/coco/dataset.yaml",
    model_size="yolov8n",  # yolov8n = fastest, yolov8s = balanced
    epochs=50,
    batch_size=8,  # Reduced for CPU efficiency
    img_size=640,
    workers=16,    # Use half your cores for data loading
    device='cpu'
):
    """
    Train YOLOv8 optimized for CPU with 32 cores
    
    YOLOv8 ALREADY IS A CNN - no need to add layers!
    It has: Backbone (CSPDarknet) + Neck (PANet) + Head (Detection)
    """
    
    print(f"{'='*60}")
    print(f"🚀 YOLOv8 CPU Training - 32 Core Optimized")
    print(f"{'='*60}")
    print(f"   Model: {model_size} (pre-trained CNN)")
    print(f"   Device: {device.upper()} (32 cores)")
    print(f"   Epochs: {epochs}")
    print(f"   Batch size: {batch_size} (optimized for CPU)")
    print(f"   DataLoader workers: {workers} (out of 32 cores)")
    print(f"\n   💡 YOLOv8 architecture:")
    print(f"      - Backbone: CSPDarknet53 (feature extraction)")
    print(f"      - Neck: PANet (feature fusion)")
    print(f"      - Head: Detection head (bounding boxes)")
    print(f"   No custom CNN layers needed - YOLO handles everything!")
    print(f"{'='*60}\n")
    
    # Verify CPU threads
    import threading
    print(f"   PyTorch threads: {torch.get_num_threads()}")
    print(f"   System CPUs: {os.cpu_count()}")
    
    # Load model (this downloads weights if needed)
    print(f"\n📥 Loading {model_size}...")
    model = YOLO(f"{model_size}.pt")
    
    # CPU-optimized training arguments
    args = {
        # Core settings
        'data': data_yaml,
        'epochs': epochs,
        'batch': batch_size,
        'imgsz': img_size,
        'device': device,
        
        # CRITICAL: Use many workers for CPU (I/O bound)
        'workers': workers,  # 16 workers = 16 cores loading data
        
        # CPU memory optimization
        'cache': False,      # Don't cache images in RAM (saves memory)
        'single_cls': True,  # Single class (product) - faster
        
        # Speed optimizations
        'pretrained': True,
        'optimizer': 'SGD',  # SGD faster than AdamW on CPU
        'lr0': 0.01,         # Higher LR for SGD
        'lrf': 0.1,
        'momentum': 0.937,
        'weight_decay': 0.0005,
        
        # Minimal augmentation for speed
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
        'mosaic': 0.0,       # DISABLE mosaic - very slow on CPU
        'mixup': 0.0,
        'copy_paste': 0.0,
        
        # Training stability
        'warmup_epochs': 1.0,  # Shorter warmup
        'patience': 5,         # Early stopping patience
        
        # Output
        'save': True,
        'project': 'models',
        'name': f'retail_inventory_{model_size}_cpu',
        'exist_ok': True,
        
        # Verbose
        'verbose': True,
    }
    
    print(f"\n⚙️  Training configuration:")
    for k, v in args.items():
        print(f"   {k}: {v}")
    print()
    
    # Train
    print(f"🚀 Starting training...\n")
    results = model.train(**args)
    
    print(f"\n{'='*60}")
    print(f"✅ Training Complete!")
    print(f"{'='*60}")
    print(f"   Best model: {results.best}")
    if hasattr(results, 'results_dict'):
        print(f"   mAP50: {results.results_dict.get('metrics/mAP50', 'N/A')}")
        print(f"   mAP50-95: {results.results_dict.get('metrics/mAP50-95', 'N/A')}")
    print(f"{'='*60}")
    
    return model, results

def fast_train_mini(data_yaml="data/coco/dataset.yaml", epochs=5):
    """
    Ultra-fast training for testing (5 epochs, tiny batch)
    Use this to verify everything works before full training
    """
    print(f"\n{'='*60}")
    print(f"⚡ MINI TRAINING - Verification Mode")
    print(f"{'='*60}")
    
    model = YOLO("yolov8n.pt")
    
    args = {
        'data': data_yaml,
        'epochs': epochs,
        'batch': 4,
        'imgsz': 320,        # Smaller images = faster
        'device': 'cpu',
        'workers': 8,
        'cache': False,
        'single_cls': True,
        'optimizer': 'SGD',
        'mosaic': 0,
        'save': True,
        'project': 'models',
        'name': 'test_run',
        'exist_ok': True,
    }
    
    results = model.train(**args)
    return model, results

def export_model(model_path, format='onnx'):
    """Export to faster formats"""
    print(f"\n📤 Exporting to {format}...")
    model = YOLO(model_path)
    
    if format == 'onnx':
        model.export(format='onnx', imgsz=640, half=False, simplify=True)
    elif format == 'openvino':
        # Intel CPU optimized format - FASTEST for inference
        model.export(format='openvino', imgsz=640, half=False)
    
    print(f"✅ Export complete!")

if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description='CPU-Optimized YOLOv8 Training')
    parser.add_argument('--data', default='data/coco/dataset.yaml', help='Dataset YAML')
    parser.add_argument('--model', default='yolov8n', choices=['yolov8n', 'yolov8s'], 
                       help='Model: n=fastest, s=balanced')
    parser.add_argument('--epochs', type=int, default=50, help='Training epochs')
    parser.add_argument('--batch', type=int, default=8, help='Batch size (4-12 for CPU)')
    parser.add_argument('--workers', type=int, default=16, help='DataLoader workers (0-32)')
    parser.add_argument('--test', action='store_true', help='Quick test run (5 epochs)')
    parser.add_argument('--export', choices=['onnx', 'openvino'], help='Export format after training')
    
    args = parser.parse_args()
    
    if args.test:
        # Quick verification run
        model, results = fast_train_mini(args.data, epochs=5)
    else:
        # Full optimized training
        model, results = train_model_cpu(
            data_yaml=args.data,
            model_size=args.model,
            epochs=args.epochs,
            batch_size=args.batch,
            workers=args.workers
        )
        
        if args.export:
            export_model(results.best, args.export)