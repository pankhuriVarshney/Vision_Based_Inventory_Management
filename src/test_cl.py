# Save as test_aggressive_learning.py
import sys
sys.path.append('.')

from continual_learning import ContinualLearner
import numpy as np
import time

def test_aggressive_learning():
    """Test that forces learning to trigger"""
    print("\n" + "="*60)
    print("🧪 AGGRESSIVE Learning Trigger Test")
    print("="*60)
    
    # Initialize with VERY LOW thresholds
    learner = ContinualLearner()
    learner.trigger_buffer_min = 20  # Very low
    learner.trigger_conf_threshold = 0.80  # HIGH threshold - will trigger easily
    learner.learning_cooldown = 5  # Short cooldown
    
    print(f"\n📊 Settings (AGGRESSIVE):")
    print(f"   Buffer min: {learner.trigger_buffer_min}")
    print(f"   Confidence threshold: {learner.trigger_conf_threshold} (HIGH - will trigger)")
    print(f"   Cooldown: {learner.learning_cooldown}s")
    
    print("\n📊 Simulating detection stream with LOW confidence...")
    
    learning_triggered = False
    
    for i in range(50):
        # Use very low confidence values
        confidence = np.random.uniform(0.3, 0.7)  # Well below threshold
        num_detections = np.random.randint(0, 3)
        
        detections = []
        for j in range(num_detections):
            detections.append({
                'bbox': [100, 100, 200, 200],
                'confidence': confidence,
                'class_id': np.random.randint(0, 5),
                'class_name': f"product_{np.random.randint(0, 5)}"
            })
        
        # Add to buffer
        learner.add_experience(detections, confidence)
        
        # Force check
        should_learn, reason = learner.should_learn()
        
        if should_learn and not learning_triggered:
            print(f"\n🎯 STEP {i}: Learning triggered!")
            print(f"   Reason: {reason}")
            print(f"   Buffer size: {learner.buffer.get_stats()['size']}")
            print(f"   Avg confidence: {learner.buffer.get_stats()['avg_confidence']:.3f}")
            
            stats = learner.learn()
            
            if stats.success:
                print(f"   ✅ Learning successful!")
                if stats.loss_before > 0:
                    print(f"   Loss improved: {stats.loss_before:.4f} → {stats.loss_after:.4f}")
            else:
                print(f"   ❌ Learning failed")
            
            learning_triggered = True
            break
        
        # Show progress every 10 steps
        if (i + 1) % 10 == 0:
            stats = learner.buffer.get_stats()
            print(f"   Step {i+1}: Buffer={stats['size']}, Conf={stats['avg_confidence']:.3f}")
        
        time.sleep(0.05)
    
    if not learning_triggered:
        print("\n⚠️ Learning still not triggered - forcing manual learning")
        print("\n🎯 Forcing manual learning...")
        stats = learner.learn()
        if stats.success:
            print(f"   ✅ Manual learning successful!")
        learning_triggered = True
    
    print("\n" + "="*60)
    print("📊 FINAL RESULTS:")
    print("="*60)
    final_stats = learner.get_stats()
    print(f"   Total Learning Events: {final_stats['total_learning_events']}")
    print(f"   Buffer Size: {final_stats['buffer']['size']}/{final_stats['buffer']['max_size']}")
    print(f"   Final Avg Confidence: {final_stats['buffer']['avg_confidence']:.3f}")
    
    return learner

def test_buffer_full_trigger():
    """Test learning triggered by buffer filling up"""
    print("\n" + "="*60)
    print("🧪 Buffer Full Trigger Test")
    print("="*60)
    
    # Small buffer to fill quickly
    learner = ContinualLearner(buffer_size=50)
    learner.trigger_buffer_min = 30
    learner.trigger_conf_threshold = 0.3  # Very low - won't trigger
    learner.learning_cooldown = 5
    
    print(f"\n📊 Settings:")
    print(f"   Buffer size: 50 (SMALL)")
    print(f"   Buffer min: {learner.trigger_buffer_min}")
    print(f"   Fill threshold: 90% (will trigger at 45 samples)")
    
    print("\n📊 Filling buffer...")
    
    for i in range(60):
        confidence = np.random.uniform(0.7, 0.9)  # High confidence
        num_detections = np.random.randint(1, 4)
        
        detections = []
        for j in range(num_detections):
            detections.append({
                'bbox': [100, 100, 200, 200],
                'confidence': confidence,
                'class_id': np.random.randint(0, 5),
                'class_name': f"product_{np.random.randint(0, 5)}"
            })
        
        learner.add_experience(detections, confidence)
        
        should_learn, reason = learner.should_learn()
        
        if should_learn:
            print(f"\n🎯 Step {i}: Learning triggered!")
            print(f"   Reason: {reason}")
            print(f"   Buffer size: {learner.buffer.get_stats()['size']}")
            print(f"   Fill percent: {learner.buffer.get_stats()['fill_percent']:.1f}%")
            
            stats = learner.learn()
            if stats.success:
                print(f"   ✅ Learning successful!")
            break
        
        if (i + 1) % 10 == 0:
            stats = learner.buffer.get_stats()
            print(f"   Step {i+1}: Buffer={stats['size']}/50 ({stats['fill_percent']:.0f}%)")
        
        time.sleep(0.05)
    
    print("\n" + "="*60)
    print("📊 FINAL RESULTS:")
    print("="*60)
    final_stats = learner.get_stats()
    print(f"   Total Learning Events: {final_stats['total_learning_events']}")
    print(f"   Buffer Size: {final_stats['buffer']['size']}/{final_stats['buffer']['max_size']}")

if __name__ == "__main__":
    print("\n" + "="*60)
    print("CONTINUAL LEARNING TEST SUITE")
    print("="*60)
    
    print("\nChoose test:")
    print("1. Low confidence trigger (aggressive thresholds)")
    print("2. Buffer full trigger (small buffer)")
    print("3. Run both tests")
    
    choice = input("\nEnter choice (1, 2, or 3): ").strip()
    
    if choice == "1":
        test_aggressive_learning()
    elif choice == "2":
        test_buffer_full_trigger()
    elif choice == "3":
        test_aggressive_learning()
        print("\n" + "="*60)
        print("Running second test...")
        print("="*60)
        test_buffer_full_trigger()
    else:
        print("Invalid choice, running both...")
        test_aggressive_learning()
        test_buffer_full_trigger()