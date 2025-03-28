from setuptools import find_packages, setup
import os
from glob import glob

package_name = 'all_nodes'

setup(
    name=package_name,
    version='0.0.0',
    packages=find_packages(exclude=['test']),
    data_files=[
        # Core package files
        (os.path.join('share', 'ament_index', 'resource_index', 'packages'),
         [os.path.join('resource', package_name)]),
        (os.path.join('share', package_name), ['package.xml']),
        
        # Launch files
        (os.path.join('share', package_name, 'launch'), 
         glob(os.path.join('launch', '*.launch.py'))),
        
        # Config files
        (os.path.join('share', package_name, 'config'),
         glob('config/*.yaml')),
         
        # Maps directory (create an empty README to ensure directory exists)
        (os.path.join('share', package_name, 'maps'),
         []),
    ],
    install_requires=['setuptools'],
    zip_safe=True,
    maintainer='ieee',
    maintainer_email='Jmarquezj545@gmail.com',
    description='Your irresistible robot control package',
    license='Apache-2.0',
    tests_require=['pytest'],
    entry_points={
        'console_scripts': [
            'mission_controller = all_nodes.mission_controller:main',
            'fire_detector = all_nodes.fire_detector_node:main',
            'hardware_diagnostics = all_nodes.hardware_diagnostics_node:main',
            'thermocouple_node = all_nodes.thermocouple_node:main',
        ],
    },
)
