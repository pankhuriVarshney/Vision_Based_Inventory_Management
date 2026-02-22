#!/usr/bin/env python3
"""
Real-time Inventory Management GUI
PyQt5-based dashboard for retail shelf monitoring
"""

import sys
import cv2
import numpy as np
from PyQt5.QtWidgets import (
    QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, 
    QLabel, QPushButton, QComboBox, QSpinBox, 
    QGroupBox, QTextEdit, QFileDialog, QProgressBar,
    QTableWidget, QTableWidgetItem, QHeaderView, QInputDialog
)
from PyQt5.QtCore import Qt, QTimer, pyqtSignal, QThread
from PyQt5.QtGui import QImage, QPixmap, QFont, QColor, QPalette
from inference import InventoryDetector, InventoryCount
import time
from collections import deque
import json

class VideoThread(QThread):
    """Thread for video processing"""
    change_pixmap_signal = pyqtSignal(np.ndarray, object)
    stats_signal = pyqtSignal(dict)
    
    def __init__(self, source, model_path, conf_threshold=0.25):
        super().__init__()
        self.source = source
        self.model_path = model_path
        self.conf_threshold = conf_threshold
        self._run_flag = True
        self.detector = None
        
    def run(self):
        self.detector = InventoryDetector(
            model_path=self.model_path,
            conf_threshold=self.conf_threshold,
        )
        
        cap = cv2.VideoCapture(self.source)
        fps_history = deque(maxlen=30)
        
        while self._run_flag:
            ret, frame = cap.read()
            if not ret:
                continue
            
            start = time.time()
            detections, annotated = self.detector.detect(frame)
            inventory = self.detector.count_inventory(detections, frame.shape)
            
            fps = 1.0 / (time.time() - start)
            fps_history.append(fps)
            avg_fps = sum(fps_history) / len(fps_history)
            
            self.change_pixmap_signal.emit(annotated, inventory)
            self.stats_signal.emit({
                'fps': avg_fps,
                'total': inventory.total_objects,
                'density': inventory.density_score,
                'timestamp': time.time()
            })
            
        cap.release()
    
    def stop(self):
        self._run_flag = False
        self.wait()

class InventoryDashboard(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("🛒 Smart Shelf Inventory System")
        self.setGeometry(100, 100, 1400, 900)
        
        # Set dark theme
        self.setStyleSheet("""
            QMainWindow {
                background-color: #1e1e1e;
            }
            QWidget {
                background-color: #2d2d2d;
                color: #ffffff;
                font-family: 'Segoe UI', Arial;
            }
            QGroupBox {
                border: 2px solid #3d3d3d;
                border-radius: 5px;
                margin-top: 10px;
                font-weight: bold;
                color: #00d4aa;
            }
            QGroupBox::title {
                subcontrol-origin: margin;
                left: 10px;
                padding: 0 5px;
            }
            QPushButton {
                background-color: #007acc;
                border: none;
                padding: 10px 20px;
                border-radius: 5px;
                color: white;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #005a9e;
            }
            QPushButton:pressed {
                background-color: #004578;
            }
            QComboBox, QSpinBox {
                background-color: #3d3d3d;
                border: 1px solid #555;
                padding: 5px;
                border-radius: 3px;
            }
            QTableWidget {
                background-color: #2d2d2d;
                border: 1px solid #3d3d3d;
                gridline-color: #3d3d3d;
            }
            QHeaderView::section {
                background-color: #007acc;
                padding: 5px;
                border: 1px solid #3d3d3d;
            }
            QTextEdit {
                background-color: #1e1e1e;
                border: 1px solid #3d3d3d;
                color: #d4d4d4;
            }
        """)
        
        self.central_widget = QWidget()
        self.setCentralWidget(self.central_widget)
        self.layout = QHBoxLayout(self.central_widget)
        
        # Left panel - Video
        self.video_panel = self._create_video_panel()
        self.layout.addWidget(self.video_panel, stretch=2)
        
        # Right panel - Controls & Stats
        self.control_panel = self._create_control_panel()
        self.layout.addWidget(self.control_panel, stretch=1)
        
        # Timer for updating charts
        self.chart_timer = QTimer()
        self.chart_timer.timeout.connect(self._update_charts)
        self.chart_timer.start(1000)  # Update every second
        
        # Data storage
        self.history_data = deque(maxlen=100)
        self.current_inventory = None
        self.thread = None
        
    def _create_video_panel(self):
        group = QGroupBox("Live Camera Feed")
        layout = QVBoxLayout()
        
        self.video_label = QLabel()
        self.video_label.setMinimumSize(800, 600)
        self.video_label.setAlignment(Qt.AlignCenter)
        self.video_label.setStyleSheet("background-color: #000; border: 2px solid #3d3d3d;")
        layout.addWidget(self.video_label)
        
        # Status bar
        self.status_label = QLabel("Status: Ready")
        self.status_label.setStyleSheet("color: #00d4aa; padding: 5px;")
        layout.addWidget(self.status_label)
        
        group.setLayout(layout)
        return group
    
    def _create_control_panel(self):
        container = QWidget()
        layout = QVBoxLayout()
        
        # Source Selection
        source_group = QGroupBox("Source Configuration")
        source_layout = QVBoxLayout()
        
        self.source_combo = QComboBox()
        self.source_combo.addItems(["Webcam (0)", "Webcam (1)", "File...", "RTSP Stream..."])
        source_layout.addWidget(QLabel("Video Source:"))
        source_layout.addWidget(self.source_combo)
        
        # UPDATED: Add your trained model to the list
        self.model_combo = QComboBox()
        self.model_combo.addItems([
            "runs/detect/models/rpc_real_labels/weights/best.pt (YOUR MODEL)",
            "yolov8n.pt (Default)",
            "Custom..."
        ])
        source_layout.addWidget(QLabel("Model:"))
        source_layout.addWidget(self.model_combo)
        
        btn_layout = QHBoxLayout()
        self.start_btn = QPushButton("▶ START")
        self.start_btn.clicked.connect(self.start_detection)
        self.stop_btn = QPushButton("⏹ STOP")
        self.stop_btn.clicked.connect(self.stop_detection)
        self.stop_btn.setEnabled(False)
        
        btn_layout.addWidget(self.start_btn)
        btn_layout.addWidget(self.stop_btn)
        source_layout.addLayout(btn_layout)
        
        source_group.setLayout(source_layout)
        layout.addWidget(source_group)
        
        # Real-time Stats
        stats_group = QGroupBox("Live Inventory Statistics")
        stats_layout = QVBoxLayout()
        
        # Total count with large font
        self.total_label = QLabel("0")
        self.total_label.setAlignment(Qt.AlignCenter)
        self.total_label.setStyleSheet("font-size: 48px; font-weight: bold; color: #00d4aa;")
        stats_layout.addWidget(QLabel("Total Items Detected:"))
        stats_layout.addWidget(self.total_label)
        
        # FPS and density
        self.fps_label = QLabel("FPS: --")
        self.density_label = QLabel("Density: --")
        stats_layout.addWidget(self.fps_label)
        stats_layout.addWidget(self.density_label)
        
        # Progress bar for shelf capacity
        stats_layout.addWidget(QLabel("Shelf Capacity:"))
        self.capacity_bar = QProgressBar()
        self.capacity_bar.setMaximum(100)
        self.capacity_bar.setStyleSheet("""
            QProgressBar {
                border: 2px solid #3d3d3d;
                border-radius: 5px;
                text-align: center;
                height: 25px;
            }
            QProgressBar::chunk {
                background-color: #00d4aa;
                border-radius: 3px;
            }
        """)
        stats_layout.addWidget(self.capacity_bar)
        
        stats_group.setLayout(stats_layout)
        layout.addWidget(stats_group)
        
        # Inventory Table
        table_group = QGroupBox("Detected Items")
        table_layout = QVBoxLayout()
        
        self.inventory_table = QTableWidget()
        self.inventory_table.setColumnCount(3)
        self.inventory_table.setHorizontalHeaderLabels(["Item ID", "Class", "Confidence"])
        self.inventory_table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        table_layout.addWidget(self.inventory_table)
        
        table_group.setLayout(table_layout)
        layout.addWidget(table_group)
        
        # Log
        log_group = QGroupBox("System Log")
        log_layout = QVBoxLayout()
        self.log_text = QTextEdit()
        self.log_text.setMaximumHeight(150)
        log_layout.addWidget(self.log_text)
        log_group.setLayout(log_layout)
        layout.addWidget(log_group)
        
        # Export button
        self.export_btn = QPushButton("💾 Export Report")
        self.export_btn.clicked.connect(self.export_report)
        layout.addWidget(self.export_btn)
        
        container.setLayout(layout)
        return container
    
    def start_detection(self):
        source_text = self.source_combo.currentText()
        
        if "Webcam" in source_text:
            source = int(source_text.split("(")[1].split(")")[0])
        elif "File" in source_text:
            file_path, _ = QFileDialog.getOpenFileName(self, "Select Video File", "", 
                                                      "Video Files (*.mp4 *.avi *.mov);;All Files (*)")
            if not file_path:
                return
            source = file_path
        else:
            source, ok = QInputDialog.getText(self, "RTSP Stream", "Enter RTSP URL:")
            if not ok or not source:
                return
        
        model_text = self.model_combo.currentText()
        if "Custom" in model_text:
            model_path, _ = QFileDialog.getOpenFileName(self, "Select Model", "", "Model Files (*.pt)")
            if not model_path:
                return
        else:
            # Extract path from combo text (first item before space)
            model_path = model_text.split()[0]
        
        self.log(f"Starting detection with source: {source}")
        self.log(f"Using model: {model_path}")
        
        self.thread = VideoThread(source, model_path)
        self.thread.change_pixmap_signal.connect(self.update_image)
        self.thread.stats_signal.connect(self.update_stats)
        self.thread.start()
        
        self.start_btn.setEnabled(False)
        self.stop_btn.setEnabled(True)
        self.status_label.setText("Status: Running 🔴")
        self.status_label.setStyleSheet("color: #ff4444;")
    
    def stop_detection(self):
        if self.thread:
            self.thread.stop()
            self.thread = None
        
        self.start_btn.setEnabled(True)
        self.stop_btn.setEnabled(False)
        self.status_label.setText("Status: Stopped")
        self.status_label.setStyleSheet("color: #ffa500;")
        self.log("Detection stopped")
    
    def update_image(self, frame, inventory):
        """Update video frame"""
        rgb_image = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        h, w, ch = rgb_image.shape
        bytes_per_line = ch * w
        qt_image = QImage(rgb_image.data, w, h, bytes_per_line, QImage.Format_RGB888)
        scaled_pixmap = QPixmap.fromImage(qt_image).scaled(
            self.video_label.size(), Qt.KeepAspectRatio, Qt.SmoothTransformation
        )
        self.video_label.setPixmap(scaled_pixmap)
        self.current_inventory = inventory
    
    def update_stats(self, stats):
        """Update statistics display"""
        self.total_label.setText(str(stats['total']))
        self.fps_label.setText(f"FPS: {stats['fps']:.1f}")
        self.density_label.setText(f"Density: {stats['density']:.1f}")
        
        # Update capacity bar (assume max 100 items for visualization)
        capacity = min(stats['total'], 100)
        self.capacity_bar.setValue(capacity)
        
        # Store history
        self.history_data.append({
            'time': stats['timestamp'],
            'count': stats['total'],
            'fps': stats['fps']
        })
        
        # Update table if inventory available
        if self.current_inventory:
            self._update_inventory_table()
    
    def _update_inventory_table(self):
        """Update the inventory table with actual detections"""
        # Clear table
        self.inventory_table.setRowCount(0)
        
        # Add rows (this is a placeholder - in real implementation you'd track individual items)
        if self.current_inventory:
            self.inventory_table.insertRow(0)
            self.inventory_table.setItem(0, 0, QTableWidgetItem("Total"))
            self.inventory_table.setItem(0, 1, QTableWidgetItem("product"))
            self.inventory_table.setItem(0, 2, QTableWidgetItem(str(self.current_inventory.total_objects)))
    
    def _update_charts(self):
        """Update trend charts (simplified)"""
        if len(self.history_data) > 1:
            counts = [d['count'] for d in self.history_data]
            avg_count = sum(counts) / len(counts)
            # Could update a matplotlib chart here
    
    def export_report(self):
        """Export inventory report"""
        if not self.history_data:
            self.log("No data to export!")
            return
        
        file_path, _ = QFileDialog.getSaveFileName(self, "Save Report", "inventory_report.json", 
                                                  "JSON Files (*.json);;CSV Files (*.csv)")
        if file_path:
            data = {
                'export_time': time.time(),
                'total_frames': len(self.history_data),
                'average_count': sum([d['count'] for d in self.history_data]) / len(self.history_data),
                'peak_count': max([d['count'] for d in self.history_data]),
                'history': list(self.history_data)
            }
            
            with open(file_path, 'w') as f:
                json.dump(data, f, indent=2)
            
            self.log(f"Report exported to {file_path}")
    
    def log(self, message):
        timestamp = time.strftime("%H:%M:%S")
        self.log_text.append(f"[{timestamp}] {message}")
    
    def closeEvent(self, event):
        self.stop_detection()
        event.accept()

def main():
    from PyQt5.QtWidgets import QApplication
    
    app = QApplication(sys.argv)
    app.setStyle('Fusion')
    
    # Set application font
    font = QFont("Segoe UI", 10)
    app.setFont(font)
    
    window = InventoryDashboard()
    window.show()
    sys.exit(app.exec_())

if __name__ == "__main__":
    main()