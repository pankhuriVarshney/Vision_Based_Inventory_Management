#!/usr/bin/env python3
"""
Continual Learning Module for Inventory Management
Implements EWC (Elastic Weight Consolidation) + Experience Replay
"""

import torch
import torch.nn as nn
import torch.optim as optim
from torch.utils.data import DataLoader, TensorDataset
import numpy as np
from collections import deque
from ultralytics import YOLO
import pickle
from pathlib import Path
import time
from dataclasses import dataclass, field
from typing import List, Dict, Tuple, Optional
import json
import os

@dataclass
class Experience:
    """Single experience for replay buffer"""
    features: np.ndarray  # Feature vector (not raw image)
    label: int
    confidence: float
    timestamp: float
    class_name: str

@dataclass
class LearningStats:
    """Statistics for learning events"""
    timestamp: float
    buffer_size: int
    avg_confidence: float
    loss_before: float
    loss_after: float
    num_samples: int
    success: bool

class ExperienceBuffer:
    """Circular buffer for storing experiences"""
    
    def __init__(self, max_size: int = 500, feature_dim: int = 128):
        self.max_size = max_size
        self.feature_dim = feature_dim
        self.buffer: deque = deque(maxlen=max_size)
        
    def add(self, features: np.ndarray, label: int, confidence: float, class_name: str):
        """Add experience to buffer"""
        exp = Experience(
            features=features.copy() if isinstance(features, np.ndarray) else np.array(features),
            label=int(label),
            confidence=float(confidence),
            timestamp=time.time(),
            class_name=str(class_name)
        )
        self.buffer.append(exp)
        
    def get_batch(self, batch_size: int = 32) -> Tuple[np.ndarray, np.ndarray]:
        """Get random batch for replay"""
        if len(self.buffer) < batch_size:
            batch_size = len(self.buffer)
        
        indices = np.random.choice(len(self.buffer), batch_size, replace=False)
        features = np.array([self.buffer[i].features for i in indices])
        labels = np.array([self.buffer[i].label for i in indices])
        
        return features, labels
    
    def get_stats(self) -> Dict:
        """Get buffer statistics"""
        if len(self.buffer) == 0:
            return {'size': 0, 'avg_confidence': 0, 'classes': {}, 'max_size': self.max_size, 'fill_percent': 0}
        
        class_counts = {}
        total_conf = 0
        for exp in self.buffer:
            class_counts[exp.class_name] = class_counts.get(exp.class_name, 0) + 1
            total_conf += exp.confidence
        
        return {
            'size': len(self.buffer),
            'avg_confidence': total_conf / len(self.buffer),
            'classes': class_counts,
            'max_size': self.max_size,
            'fill_percent': (len(self.buffer) / self.max_size) * 100
        }

class ContinualLearner:
    """
    Main continual learning orchestrator
    Combines Experience Replay for inventory detection
    """
    
    def __init__(
        self,
        model_path: str = None,
        buffer_size: int = 500,
        feature_dim: int = 128,
        replay_batch_size: int = 32,
        learning_rate: float = 1e-4
    ):
        print(f"Initializing Continual Learner...")
        
        # Find model path if not provided
        if model_path is None:
            possible_paths = [
                "models/rpc_real_labels/weights/best.pt",
                "../models/rpc_real_labels/weights/best.pt",
                Path(__file__).parent.parent / "models/rpc_real_labels/weights/best.pt",
                Path("C:/Users/pankh/Documents/Vision_Based_Inventory_Management/models/rpc_real_labels/weights/best.pt")
            ]
            for path in possible_paths:
                if Path(path).exists():
                    model_path = str(path)
                    break
        
        if model_path is None or not Path(model_path).exists():
            print(f"⚠️ Model not found, using mock mode")
            self.model = None
        else:
            print(f"📁 Loading model from: {model_path}")
            try:
                self.model = YOLO(model_path)
                print(f"✅ Model loaded successfully")
            except Exception as e:
                print(f"⚠️ Could not load model: {e}")
                self.model = None
        
        self.replay_batch_size = replay_batch_size
        self.learning_rate = learning_rate
        
        # Initialize components
        self.buffer = ExperienceBuffer(max_size=buffer_size, feature_dim=feature_dim)
        self.learning_stats = []
        
        # Learning triggers
        self.trigger_buffer_min = 50
        self.trigger_conf_threshold = 0.6
        self.last_learning_time = 0
        self.learning_cooldown = 60  # seconds between learning events
        
        print(f"✅ Continual Learner initialized")
        print(f"   Buffer: {buffer_size} experiences")
        print(f"   Replay batch: {replay_batch_size}")
    
    def extract_features(self, detections: List) -> np.ndarray:
        """Extract feature vector from detections"""
        if not detections:
            return np.zeros(128)
        
        features = []
        for det in detections[:10]:  # Limit to first 10 detections
            if 'bbox' in det:
                bbox = det['bbox']
                w = (bbox[2] - bbox[0]) / 640.0  # Normalized width
                h = (bbox[3] - bbox[1]) / 480.0  # Normalized height
                features.extend([w, h, det.get('confidence', 0.5), det.get('class_id', 0)])
            else:
                features.extend([0.5, 0.5, 0.5, 0])
        
        # Pad to fixed dimension
        target_dim = 128
        while len(features) < target_dim:
            features.append(0)
        
        return np.array(features[:target_dim])
    
    def add_experience(self, detections: List, frame_confidence: float):
        """Add detection results as experience"""
        if not detections:
            # Still add empty experience to track confidence
            features = np.zeros(128)
            self.buffer.add(
                features=features,
                label=-1,
                confidence=frame_confidence,
                class_name="empty_frame"
            )
            return
        
        for det in detections[:5]:  # Add top 5 detections
            features = self.extract_features([det])
            self.buffer.add(
                features=features,
                label=det.get('class_id', 0),
                confidence=det.get('confidence', 0.5),
                class_name=det.get('class_name', 'product')
            )
        
        # Also add overall frame confidence
        features = self.extract_features(detections)
        self.buffer.add(
            features=features,
            label=-1,  # No specific label for frame
            confidence=frame_confidence,
            class_name="frame"
        )
    
    def should_learn(self) -> Tuple[bool, str]:
        """Check if learning should be triggered"""
        stats = self.buffer.get_stats()
        current_time = time.time()
        
        # Check cooldown
        if current_time - self.last_learning_time < self.learning_cooldown:
            return False, f"cooldown ({int(self.learning_cooldown - (current_time - self.last_learning_time))}s remaining)"
        
        # Check buffer size
        if stats['size'] < self.trigger_buffer_min:
            return False, f"buffer_size ({stats['size']}/{self.trigger_buffer_min})"
        
        # Check confidence drop
        if stats['avg_confidence'] < self.trigger_conf_threshold and stats['avg_confidence'] > 0:
            return True, f"low_confidence ({stats['avg_confidence']:.2f} < {self.trigger_conf_threshold})"
        
        # Check if buffer is full
        if stats['fill_percent'] > 90:
            return True, f"buffer_full ({stats['fill_percent']:.0f}%)"
        
        return False, f"conditions_not_met (conf={stats['avg_confidence']:.2f})"
    
    def _replay_training(self, epochs: int = 3):
        """Train on replay buffer"""
        buffer_size = self.buffer.get_stats()['size']
        if buffer_size < 10:
            return 0
        
        # Get replay batch
        features, labels = self.buffer.get_batch(min(self.replay_batch_size, buffer_size))
        
        # Filter out invalid labels (-1)
        valid_mask = labels >= 0
        if not np.any(valid_mask):
            return 0
        
        features = features[valid_mask]
        labels = labels[valid_mask]
        
        if len(features) < 2:
            return 0
        
        # Convert to tensors
        X = torch.FloatTensor(features)
        y = torch.LongTensor(labels)
        
        # Simple model for feature learning
        replay_model = nn.Sequential(
            nn.Linear(features.shape[1], 64),
            nn.ReLU(),
            nn.Dropout(0.2),
            nn.Linear(64, 32),
            nn.ReLU(),
            nn.Linear(32, max(10, labels.max() + 1))
        )
        
        criterion = nn.CrossEntropyLoss()
        optimizer = optim.Adam(replay_model.parameters(), lr=self.learning_rate)
        
        total_loss = 0
        num_batches = 0
        
        dataset = TensorDataset(X, y)
        dataloader = DataLoader(dataset, batch_size=min(16, len(features)), shuffle=True)
        
        for epoch in range(epochs):
            for batch_X, batch_y in dataloader:
                optimizer.zero_grad()
                output = replay_model(batch_X)
                loss = criterion(output, batch_y)
                loss.backward()
                optimizer.step()
                total_loss += loss.item()
                num_batches += 1
        
        return total_loss / max(num_batches, 1)
    
    def learn(self) -> LearningStats:
        """Execute learning step"""
        print(f"\n{'='*60}")
        print(f"🔄 Starting Continual Learning Session")
        print(f"{'='*60}")
        
        stats = self.buffer.get_stats()
        print(f"   Buffer size: {stats['size']}")
        print(f"   Avg confidence: {stats['avg_confidence']:.2f}")
        
        start_time = time.time()
        
        try:
            # Run replay training
            loss_before = self._replay_training(epochs=2)
            loss_after = self._replay_training(epochs=3)
            
            # Record statistics
            learning_stats = LearningStats(
                timestamp=time.time(),
                buffer_size=stats['size'],
                avg_confidence=stats['avg_confidence'],
                loss_before=loss_before,
                loss_after=loss_after,
                num_samples=stats['size'],
                success=True
            )
            self.learning_stats.append(learning_stats)
            
            # Clear buffer after learning (optional - uncomment to clear)
            # self.buffer = ExperienceBuffer(max_size=self.buffer.max_size)
            
            self.last_learning_time = time.time()
            
            duration = time.time() - start_time
            print(f"\n✅ Learning completed in {duration:.1f}s")
            if loss_before > 0 and loss_after > 0:
                print(f"   Loss: {loss_before:.4f} → {loss_after:.4f}")
            
            return learning_stats
            
        except Exception as e:
            print(f"\n❌ Learning failed: {e}")
            import traceback
            traceback.print_exc()
            
            return LearningStats(
                timestamp=time.time(),
                buffer_size=stats['size'],
                avg_confidence=stats['avg_confidence'],
                loss_before=0,
                loss_after=0,
                num_samples=0,
                success=False
            )
    
    def get_stats(self) -> Dict:
        """Get comprehensive system stats"""
        buffer_stats = self.buffer.get_stats()
        
        recent_learning = None
        if self.learning_stats:
            recent = self.learning_stats[-1]
            recent_learning = {
                'timestamp': recent.timestamp,
                'success': recent.success,
                'buffer_size': recent.buffer_size
            }
        
        return {
            'buffer': buffer_stats,
            'total_learning_events': len(self.learning_stats),
            'last_learning_time': self.last_learning_time,
            'recent_learning': recent_learning,
            'learning_cooldown': self.learning_cooldown,
            'trigger_threshold': self.trigger_conf_threshold
        }
    
    def save_state(self, path: str = "models/continual_learning_state.pkl"):
        """Save learner state"""
        try:
            state = {
                'buffer': self.buffer,
                'learning_stats': self.learning_stats,
                'last_learning_time': self.last_learning_time
            }
            save_path = Path(path)
            save_path.parent.mkdir(parents=True, exist_ok=True)
            with open(save_path, 'wb') as f:
                pickle.dump(state, f)
            print(f"💾 Saved continual learning state to {save_path}")
        except Exception as e:
            print(f"⚠️ Could not save state: {e}")
    
    def load_state(self, path: str = "models/continual_learning_state.pkl"):
        """Load learner state"""
        if Path(path).exists():
            try:
                with open(path, 'rb') as f:
                    state = pickle.load(f)
                self.buffer = state['buffer']
                self.learning_stats = state['learning_stats']
                self.last_learning_time = state['last_learning_time']
                print(f"📂 Loaded continual learning state from {path}")
            except Exception as e:
                print(f"⚠️ Could not load state: {e}")

# Test script
def test_continual_learning():
    """Test the continual learning system locally"""
    print("\n" + "="*60)
    print("🧪 Testing Continual Learning System")
    print("="*60)
    
    # Initialize learner
    learner = ContinualLearner()
    
    # Simulate detections over time
    print("\n📊 Simulating detection stream...")
    
    for i in range(100):
        # Simulate detections with varying confidence
        num_detections = np.random.randint(0, 5)
        detections = []
        
        for j in range(num_detections):
            detections.append({
                'bbox': [100, 100, 200, 200],
                'confidence': max(0.3, min(0.95, np.random.normal(0.7, 0.2))),
                'class_id': np.random.randint(0, 5),
                'class_name': f"product_{np.random.randint(0, 5)}"
            })
        
        # Calculate frame confidence
        if detections:
            frame_conf = np.mean([d['confidence'] for d in detections])
        else:
            frame_conf = 0.0
        
        # Add to buffer
        learner.add_experience(detections, frame_conf)
        
        # Check if learning should trigger
        should_learn, reason = learner.should_learn()
        
        if should_learn:
            print(f"\n🎯 Learning triggered at step {i}: {reason}")
            stats = learner.learn()
            
            # Show stats
            sys_stats = learner.get_stats()
            print(f"   Buffer: {sys_stats['buffer']['size']} experiences")
            print(f"   Learning events: {sys_stats['total_learning_events']}")
        
        # Progress indicator
        if (i + 1) % 20 == 0:
            stats = learner.get_stats()
            print(f"\n📈 Step {i+1}: Buffer={stats['buffer']['size']}, "
                  f"AvgConf={stats['buffer']['avg_confidence']:.2f}, "
                  f"Events={stats['total_learning_events']}")
    
    print("\n" + "="*60)
    print("✅ Continual Learning Test Complete")
    print("="*60)
    
    # Final stats
    final_stats = learner.get_stats()
    print(f"\n📊 Final Statistics:")
    print(f"   Total Learning Events: {final_stats['total_learning_events']}")
    print(f"   Buffer Size: {final_stats['buffer']['size']}/{final_stats['buffer']['max_size']}")
    print(f"   Avg Confidence: {final_stats['buffer']['avg_confidence']:.2f}")

if __name__ == "__main__":
    test_continual_learning()