#!/usr/bin/env python3
"""
Enhanced Test Script for Continual Learning with Graph Generation
"""

import sys
sys.path.append('.')

from continual_learning import ContinualLearner
import numpy as np
import time
import matplotlib.pyplot as plt
from pathlib import Path

def test_aggressive_learning():
    """Test that forces learning to trigger with graph output"""
    print("\n" + "="*60)
    print("🧪 AGGRESSIVE Learning Trigger Test")
    print("="*60)
    
    learner = ContinualLearner()
    learner.trigger_buffer_min = 20
    learner.trigger_conf_threshold = 0.80
    learner.learning_cooldown = 5
    
    print(f"\n📊 Settings (AGGRESSIVE):")
    print(f"   Buffer min: {learner.trigger_buffer_min}")
    print(f"   Confidence threshold: {learner.trigger_conf_threshold}")
    print(f"   Cooldown: {learner.learning_cooldown}s")
    
    print("\n📊 Simulating detection stream with LOW confidence...")
    
    learning_triggered = False
    
    for i in range(50):
        confidence = np.random.uniform(0.3, 0.7)
        num_detections = np.random.randint(0, 3)
        
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
    
    # Generate graphs
    learner.generate_report_graphs(output_dir="results/aggressive_test")
    
    return learner

def test_buffer_full_trigger():
    """Test learning triggered by buffer filling up with graph output"""
    print("\n" + "="*60)
    print("🧪 Buffer Full Trigger Test")
    print("="*60)
    
    learner = ContinualLearner(buffer_size=50)
    learner.trigger_buffer_min = 30
    learner.trigger_conf_threshold = 0.3
    learner.learning_cooldown = 5
    
    print(f"\n📊 Settings:")
    print(f"   Buffer size: 50 (SMALL)")
    print(f"   Buffer min: {learner.trigger_buffer_min}")
    print(f"   Fill threshold: 90% (will trigger at 45 samples)")
    
    print("\n📊 Filling buffer...")
    
    for i in range(60):
        confidence = np.random.uniform(0.7, 0.9)
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
    
    # Generate graphs
    learner.generate_report_graphs(output_dir="results/buffer_full_test")
    
    return learner

def generate_comparison_graph(learner1, learner2, output_dir="results/comparison"):
    """Generate comparison graph between two test runs"""
    Path(output_dir).mkdir(parents=True, exist_ok=True)
    
    fig, axes = plt.subplots(2, 2, figsize=(14, 10))
    
    # Confidence comparison
    ax = axes[0, 0]
    if learner1.timestamps:
        t1 = [t - learner1.timestamps[0] for t in learner1.timestamps]
        ax.plot(t1, learner1.confidence_history, 'b-', label='Aggressive Test', linewidth=2)
    if learner2.timestamps:
        t2 = [t - learner2.timestamps[0] for t in learner2.timestamps]
        ax.plot(t2, learner2.confidence_history, 'r-', label='Buffer Full Test', linewidth=2)
    ax.set_xlabel('Time (s)')
    ax.set_ylabel('Confidence')
    ax.set_title('Confidence Comparison')
    ax.legend()
    ax.grid(True, alpha=0.3)
    
    # Buffer size comparison
    ax = axes[0, 1]
    if learner1.timestamps:
        t1 = [t - learner1.timestamps[0] for t in learner1.timestamps]
        ax.plot(t1, learner1.buffer_size_history, 'b-', label='Aggressive Test', linewidth=2)
    if learner2.timestamps:
        t2 = [t - learner2.timestamps[0] for t in learner2.timestamps]
        ax.plot(t2, learner2.buffer_size_history, 'r-', label='Buffer Full Test', linewidth=2)
    ax.set_xlabel('Time (s)')
    ax.set_ylabel('Buffer Size')
    ax.set_title('Buffer Size Comparison')
    ax.legend()
    ax.grid(True, alpha=0.3)
    
    # Learning events comparison
    ax = axes[1, 0]
    tests = ['Aggressive\n(Low Conf)', 'Buffer Full\n(High Cap)']
    events = [len(learner1.learning_stats), len(learner2.learning_stats)]
    colors = ['blue', 'red']
    ax.bar(tests, events, color=colors, alpha=0.7)
    ax.set_ylabel('Number of Learning Events')
    ax.set_title('Learning Events Comparison')
    ax.grid(True, alpha=0.3)
    
    # Summary table
    ax = axes[1, 1]
    ax.axis('off')
    
    data = [
        ['Metric', 'Aggressive Test', 'Buffer Full Test'],
        ['Total Events', str(len(learner1.learning_stats)), str(len(learner2.learning_stats))],
        ['Final Buffer', str(learner1.buffer.get_stats()['size']), str(learner2.buffer.get_stats()['size'])],
        ['Final Confidence', f"{learner1.buffer.get_stats()['avg_confidence']:.3f}", 
         f"{learner2.buffer.get_stats()['avg_confidence']:.3f}"],
        ['Trigger Type', 'Low Confidence', 'Buffer Capacity']
    ]
    
    table = ax.table(cellText=data, cellLoc='center', loc='center',
                    colWidths=[0.3, 0.35, 0.35])
    table.auto_set_font_size(False)
    table.set_fontsize(10)
    table.scale(1, 2)
    
    # Style header row
    for i in range(3):
        table[(0, i)].set_facecolor('#40466e')
        table[(0, i)].set_text_props(weight='bold', color='white')
    
    ax.set_title('Test Comparison Summary', fontsize=12, fontweight='bold', pad=20)
    
    plt.tight_layout()
    plt.savefig(f'{output_dir}/test_comparison.png', dpi=300, bbox_inches='tight')
    plt.close()
    
    print(f"\n📊 Comparison graph saved to: {output_dir}/test_comparison.png")

if __name__ == "__main__":
    print("\n" + "="*60)
    print("CONTINUAL LEARNING TEST SUITE WITH GRAPHS")
    print("="*60)
    
    print("\nChoose test:")
    print("1. Low confidence trigger (aggressive thresholds)")
    print("2. Buffer full trigger (small buffer)")
    print("3. Run both tests + comparison")
    
    choice = input("\nEnter choice (1, 2, or 3): ").strip()
    
    if choice == "1":
        test_aggressive_learning()
    elif choice == "2":
        test_buffer_full_trigger()
    elif choice == "3":
        learner1 = test_aggressive_learning()
        print("\n" + "="*60)
        print("Running second test...")
        print("="*60)
        learner2 = test_buffer_full_trigger()
        
        print("\n" + "="*60)
        print("Generating comparison graph...")
        print("="*60)
        generate_comparison_graph(learner1, learner2)
    else:
        print("Invalid choice, running both...")
        learner1 = test_aggressive_learning()
        learner2 = test_buffer_full_trigger()
        generate_comparison_graph(learner1, learner2)