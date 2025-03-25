from setuptools import setup
import os
from glob import glob

package_name = 'esp32_interface'

setup(
    name=package_name,
    version='0.0.1',
    packages=[package_name],
    data_files=[
        ('share/ament_index/resource_index/packages',
            ['resource/' + package_name]),
        ('share/' + package_name, ['package.xml']),
        (os.path.join('share', package_name, 'launch'), glob('launch/*.py')),
    ],
    install_requires=['setuptools'],
    zip_safe=True,
    maintainer='ieee',
    maintainer_email='user@todo.todo',
    description='Package for interfacing with ESP32 encoder data and controlling motors',
    license='TODO: License declaration',
    tests_require=['pytest'],
    entry_points={
        'console_scripts': [
            'esp32_odometry_node = esp32_interface.esp32_odometry_node:main',
        ],
    },
) 