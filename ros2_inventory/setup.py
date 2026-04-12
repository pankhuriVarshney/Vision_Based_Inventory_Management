from setuptools import find_packages, setup
from glob import glob
import os

package_name = 'ros2_inventory'

setup(
    name=package_name,
    version='1.1.0',
    packages=find_packages(exclude=['test']),
    data_files=[
        ('share/ament_index/resource_index/packages', ['resource/' + package_name]),
        ('share/' + package_name, ['package.xml']),
        (os.path.join('share', package_name, 'launch'), glob('launch/*.launch.py')),
        (os.path.join('share', package_name, 'config'), glob('config/*.yaml')),
    ],
    install_requires=['setuptools'],
    zip_safe=True,
    maintainer='Your Name',
    maintainer_email='your.email@example.com',
    description='ROS2 package for Vision-Based Inventory Management with Pan-Tilt',
    license='MIT',
    tests_require=['pytest'],
    entry_points={
        'console_scripts': [
            'camera_node = ros2_inventory.camera_node:main',
            'pi_camera_node = ros2_inventory.camera_node_picamera2:main',
            'detection_node = ros2_inventory.detection_node:main',
            'inventory_node = ros2_inventory.inventory_node:main',
            'api_bridge_node = ros2_inventory.api_bridge_node:main',
            'pan_tilt_controller = ros2_inventory.pan_tilt_controller:main',  # NEW
        ],
    },
)