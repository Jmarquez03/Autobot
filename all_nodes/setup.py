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
        
        # Config files - include both yaml and rviz files
        (os.path.join('share', package_name, 'config'),
         glob('config/*.yaml') + glob('config/*.rviz')),
         
        # # Add these steamy extras for full compliance
        # (os.path.join('share', package_name, 'meshes'), 
        #  glob('meshes/*')),
        # (os.path.join('share', package_name, 'urdf'), 
        #  glob('urdf/*')),
    ],
    install_requires=['setuptools'],
    zip_safe=True,
    maintainer='ieee',
    maintainer_email='Jmarquezj545@gmail.com',
    description='Central package for launching all robot components',
    license='Apache-2.0',
    tests_require=['pytest'],
    entry_points={
        'console_scripts': [
            # Remove incorrect launch entry point
        ],
    },
)
