cd ~/ros2_ws
colcon build --packages-select ros2_inventory
source install/setup.bash

ros2 launch ros2_inventory inventory_system.launch.py


cd ~/Vision_Based_Inventory_Management
source venv/bin/activate
python3 -m uvicorn src.api:app --host 0.0.0.0 --port 8000


sudo apt install --reinstall ros-jazzy-cv-bridge

cd ~/Vision_Based_Inventory_Management
source venv/bin/activate
pip install --force-reinstall 'numpy<2.0'
deactivate
