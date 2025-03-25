from setuptools import setup
import os
from glob import glob

package_name = 'robot_killer'

setup(
    name=package_name,
    version='0.0.1',
    packages=[package_name],
    data_files=[
        ('share/ament_index/resource_index/packages',
            ['resource/' + package_name]),
        ('share/' + package_name, ['package.xml']),
        # Include all launch files
        (os.path.join('share', package_name, 'launch'),
         glob(os.path.join('launch', '*.launch.py'))),
        # Include all config files
        (os.path.join('share', package_name, 'config'),
         glob(os.path.join('config', '*.yaml'))),
        # Include URDF files
        (os.path.join('share', package_name, 'urdf'),
         glob(os.path.join('urdf', '*.urdf.xml'))),
    ],
    install_requires=['setuptools'],
    zip_safe=True,
    maintainer='your_name',
    maintainer_email='zavala_esteban4455@yahoo.com',
    description='Brief package description',
    license='TODO: License declaration',
    tests_require=['pytest'],
    entry_points={
        'console_scripts': [
            'mission_controller = robot_killer.mission_controller:main',
            'fire_detector_node = robot_killer.fire_deector_node:main',
            'temperature_simulator = robot_killer.temerature_simulator:main',
            'my_node = robot_killer.my_node:main',
        ],
    },
)
