#!/usr/bin/env python3
"""
Model Export Script for Inventory Management System
Exports YOLOv8 models to various formats for deployment:
- TFLite (for Raspberry Pi / Edge devices)
- ONNX (for cross-platform compatibility)
- OpenVINO (for Intel hardware)
- TensorRT (for NVIDIA Jetson)

Usage:
    python export_model.py --model models/rpc_real_labels/weights/best.pt --format tflite
    python export_model.py --model yolov8n.pt --format all
"""

import argparse
import sys
from pathlib import Path
from ultralytics import YOLO


def export_to_tflite(model_path: str, output_dir: str = "models/exported", imgsz: int = 640, int8: bool = True):
    """
    Export model to TensorFlow Lite format
    
    Args:
        model_path: Path to PyTorch model (.pt)
        output_dir: Directory to save exported model
        imgsz: Image size for inference
        int8: Use INT8 quantization (smaller, faster)
    """
    print(f"\n{'='*60}")
    print(f"Exporting to TFLite (INT8={int8})")
    print(f"{'='*60}")
    
    try:
        # Load model
        model = YOLO(model_path)
        
        # Export
        print(f"Exporting {model_path}...")
        tflite_path = model.export(
            format='tflite',
            imgsz=imgsz,
            half=False,  # FP16 not supported in TFLite
            int8=int8,
            optimize=True,
        )
        
        print(f"\n✅ TFLite export successful!")
        print(f"   Model: {tflite_path}")
        
        # Get file size
        import os
        size_mb = os.path.getsize(tflite_path) / (1024 * 1024)
        print(f"   Size: {size_mb:.2f} MB")
        
        return tflite_path
    
    except Exception as e:
        print(f"\n❌ TFLite export failed: {e}")
        return None


def export_to_onnx(model_path: str, output_dir: str = "models/exported", imgsz: int = 640, simplify: bool = True):
    """
    Export model to ONNX format
    
    Args:
        model_path: Path to PyTorch model (.pt)
        output_dir: Directory to save exported model
        imgsz: Image size for inference
        simplify: Simplify ONNX model
    """
    print(f"\n{'='*60}")
    print(f"Exporting to ONNX")
    print(f"{'='*60}")
    
    try:
        # Load model
        model = YOLO(model_path)
        
        # Export
        print(f"Exporting {model_path}...")
        onnx_path = model.export(
            format='onnx',
            imgsz=imgsz,
            simplify=simplify,
        )
        
        print(f"\n✅ ONNX export successful!")
        print(f"   Model: {onnx_path}")
        
        # Get file size
        import os
        size_mb = os.path.getsize(onnx_path) / (1024 * 1024)
        print(f"   Size: {size_mb:.2f} MB")
        
        return onnx_path
    
    except Exception as e:
        print(f"\n❌ ONNX export failed: {e}")
        return None


def export_to_openvino(model_path: str, output_dir: str = "models/exported", imgsz: int = 640):
    """
    Export model to OpenVINO format (Intel hardware)
    
    Args:
        model_path: Path to PyTorch model (.pt)
        output_dir: Directory to save exported model
        imgsz: Image size for inference
    """
    print(f"\n{'='*60}")
    print(f"Exporting to OpenVINO (Intel Hardware)")
    print(f"{'='*60}")
    
    try:
        # Load model
        model = YOLO(model_path)
        
        # Export
        print(f"Exporting {model_path}...")
        ov_path = model.export(
            format='openvino',
            imgsz=imgsz,
        )
        
        print(f"\n✅ OpenVINO export successful!")
        print(f"   Model: {ov_path}")
        
        return ov_path
    
    except Exception as e:
        print(f"\n❌ OpenVINO export failed: {e}")
        print(f"   Note: Install openvino-dev: pip install openvino-dev")
        return None


def export_to_tensorrt(model_path: str, output_dir: str = "models/exported", imgsz: int = 640, half: bool = True):
    """
    Export model to TensorRT format (NVIDIA Jetson)
    
    Args:
        model_path: Path to PyTorch model (.pt)
        output_dir: Directory to save exported model
        imgsz: Image size for inference
        half: Use FP16 precision
    """
    print(f"\n{'='*60}")
    print(f"Exporting to TensorRT (NVIDIA Jetson)")
    print(f"{'='*60}")
    
    try:
        # Load model
        model = YOLO(model_path)
        
        # Export
        print(f"Exporting {model_path}...")
        trt_path = model.export(
            format='engine',
            imgsz=imgsz,
            half=half,
            device='cuda',
        )
        
        print(f"\n✅ TensorRT export successful!")
        print(f"   Model: {trt_path}")
        
        return trt_path
    
    except Exception as e:
        print(f"\n❌ TensorRT export failed: {e}")
        print(f"   Note: Requires NVIDIA GPU with CUDA")
        return None


def export_to_torchscript(model_path: str, output_dir: str = "models/exported", imgsz: int = 640, half: bool = False):
    """
    Export model to TorchScript format (PyTorch native)
    
    Args:
        model_path: Path to PyTorch model (.pt)
        output_dir: Directory to save exported model
        imgsz: Image size for inference
        half: Use FP16 precision
    """
    print(f"\n{'='*60}")
    print(f"Exporting to TorchScript")
    print(f"{'='*60}")
    
    try:
        # Load model
        model = YOLO(model_path)
        
        # Export
        print(f"Exporting {model_path}...")
        ts_path = model.export(
            format='torchscript',
            imgsz=imgsz,
            half=half,
        )
        
        print(f"\n✅ TorchScript export successful!")
        print(f"   Model: {ts_path}")
        
        return ts_path
    
    except Exception as e:
        print(f"\n❌ TorchScript export failed: {e}")
        return None


def benchmark_model(model_path: str, device: str = 'cpu', imgsz: int = 640, runs: int = 100):
    """
    Benchmark model inference speed
    
    Args:
        model_path: Path to model
        device: Device to run on (cpu, cuda)
        imgsz: Image size
        runs: Number of runs for benchmark
    """
    print(f"\n{'='*60}")
    print(f"Benchmarking Model Performance")
    print(f"{'='*60}")
    print(f"   Model: {model_path}")
    print(f"   Device: {device}")
    print(f"   Image Size: {imgsz}")
    print(f"   Runs: {runs}")
    
    try:
        import time
        import numpy as np
        import cv2
        
        # Load model
        model = YOLO(model_path)
        
        # Create dummy image
        dummy_img = np.random.randint(0, 255, (imgsz, imgsz, 3), dtype=np.uint8)
        
        # Warmup
        print("\n   Warming up...")
        for _ in range(10):
            model(dummy_img, verbose=False, device=device)
        
        # Benchmark
        print(f"   Running benchmark ({runs} iterations)...")
        times = []
        
        for i in range(runs):
            start = time.time()
            model(dummy_img, verbose=False, device=device)
            elapsed = (time.time() - start) * 1000  # ms
            times.append(elapsed)
        
        # Statistics
        avg_time = sum(times) / len(times)
        min_time = min(times)
        max_time = max(times)
        fps = 1000 / avg_time if avg_time > 0 else 0
        
        print(f"\n{'='*60}")
        print(f"   Results:")
        print(f"   Average: {avg_time:.2f}ms ({fps:.1f} FPS)")
        print(f"   Min: {min_time:.2f}ms")
        print(f"   Max: {max_time:.2f}ms")
        print(f"{'='*60}")
        
        return {
            'avg_ms': avg_time,
            'min_ms': min_time,
            'max_ms': max_time,
            'fps': fps
        }
    
    except Exception as e:
        print(f"\n❌ Benchmark failed: {e}")
        return None


def main():
    parser = argparse.ArgumentParser(description='Export YOLOv8 models for deployment')
    
    parser.add_argument('--model', type=str, required=True,
                       help='Path to PyTorch model (.pt file)')
    parser.add_argument('--format', type=str, default='tflite',
                       choices=['tflite', 'onnx', 'openvino', 'tensorrt', 'torchscript', 'all'],
                       help='Export format')
    parser.add_argument('--imgsz', type=int, default=640,
                       help='Image size for inference')
    parser.add_argument('--int8', action='store_true',
                       help='Use INT8 quantization (TFLite only)')
    parser.add_argument('--benchmark', action='store_true',
                       help='Run benchmark after export')
    parser.add_argument('--device', type=str, default='cpu',
                       choices=['cpu', 'cuda'],
                       help='Device for benchmark')
    parser.add_argument('--output', type=str, default='models/exported',
                       help='Output directory')
    
    args = parser.parse_args()
    
    # Verify model exists
    if not Path(args.model).exists():
        print(f"\n❌ Model not found: {args.model}")
        sys.exit(1)
    
    print(f"\n╔═══════════════════════════════════════════════════════════╗")
    print(f"║   Model Export Tool for Inventory Management              ║")
    print(f"╚═══════════════════════════════════════════════════════════╝")
    print(f"\n   Source: {args.model}")
    print(f"   Format: {args.format}")
    print(f"   Image Size: {args.imgsz}")
    
    # Export based on format
    exported_path = None
    
    if args.format == 'tflite':
        exported_path = export_to_tflite(args.model, args.output, args.imgsz, args.int8)
    elif args.format == 'onnx':
        exported_path = export_to_onnx(args.model, args.output, args.imgsz)
    elif args.format == 'openvino':
        exported_path = export_to_openvino(args.model, args.output, args.imgsz)
    elif args.format == 'tensorrt':
        exported_path = export_to_tensorrt(args.model, args.output, args.imgsz)
    elif args.format == 'torchscript':
        exported_path = export_to_torchscript(args.model, args.output, args.imgsz)
    elif args.format == 'all':
        # Export to all formats
        formats = ['tflite', 'onnx', 'torchscript']
        
        for fmt in formats:
            try:
                if fmt == 'tflite':
                    export_to_tflite(args.model, args.output, args.imgsz, args.int8)
                elif fmt == 'onnx':
                    export_to_onnx(args.model, args.output, args.imgsz)
                elif fmt == 'torchscript':
                    export_to_torchscript(args.model, args.output, args.imgsz)
            except Exception as e:
                print(f"\n⚠️  Failed to export to {fmt}: {e}")
    
    # Run benchmark
    if args.benchmark and exported_path:
        benchmark_model(exported_path, args.device, args.imgsz)
    
    print(f"\n✅ Export complete!")
    print(f"\n💡 Deployment Tips:")
    print(f"   • TFLite: Best for Raspberry Pi, mobile devices")
    print(f"   • ONNX: Universal format, works everywhere")
    print(f"   • OpenVINO: Intel CPUs, NCS2 sticks")
    print(f"   • TensorRT: NVIDIA Jetson boards")
    print(f"   • TorchScript: PyTorch native deployment")


if __name__ == "__main__":
    main()
