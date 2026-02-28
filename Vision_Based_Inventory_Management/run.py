#!/usr/bin/env python3
"""
One-click launcher for Retail Inventory System
Usage: python run.py [preprocess|train|detect|gui]
"""

import sys
import subprocess
import argparse
from pathlib import Path

def main():
    parser = argparse.ArgumentParser(description='Retail Inventory System')
    parser.add_argument('command', choices=['setup', 'preprocess', 'train', 'detect', 'gui', 'all'],
                       help='Command to run')
    parser.add_argument('--source', default='0', help='Video source for detection')
    parser.add_argument('--model', default='yolov8n.pt', help='Model to use')
    
    args = parser.parse_args()
    
    if args.command == 'setup':
        print("🔧 Installing dependencies...")
        subprocess.run([sys.executable, "-m", "pip", "install", "-r", "requirements.txt"])
        print("✅ Setup complete!")
    
    elif args.command == 'preprocess':
        print("📊 Running preprocessing...")
        subprocess.run([sys.executable, "src/preprocess.py"])
    
    elif args.command == 'train':
        print("🚀 Starting training...")
        subprocess.run([sys.executable, "src/train.py", "--epochs", "50"])
    
    elif args.command == 'detect':
        print("🔍 Starting detection...")
        subprocess.run([sys.executable, "src/inference.py", 
                       "--source", args.source, 
                       "--model", args.model])
    
    elif args.command == 'gui':
        print("🖥️  Launching GUI...")
        subprocess.run([sys.executable, "src/gui.py"])
    
    elif args.command == 'all':
        print("🎯 Running full pipeline...")
        # Setup
        subprocess.run([sys.executable, "-m", "pip", "install", "-r", "requirements.txt"])
        # Preprocess
        subprocess.run([sys.executable, "src/preprocess.py"])
        # Train (quick version)
        subprocess.run([sys.executable, "src/train.py", "--epochs", "10"])
        # Launch GUI
        subprocess.run([sys.executable, "src/gui.py"])

if __name__ == "__main__":
    main()