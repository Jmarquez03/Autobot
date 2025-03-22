from setuptools import find_packages, setup

package_name = 'twist_to_ackermann'

setup(
    name=package_name,
    version='0.0.0',
    packages=find_packages(exclude=['test']),
    data_files=[
        ('share/ament_index/resource_index/packages',
            ['resource/' + package_name]),
        ('share/' + package_name, ['package.xml']),
    ],
    install_requires=['setuptools'],
    zip_safe=True,
    maintainer='ieee',
    maintainer_email='Jmarquezj545@gmail.com',
    description='TODO: Package description',
    license='TODO: License declaration',
    tests_require=['pytest'],
    entry_points={
        'console_scripts': [
            'twist_to_ackermann_converter = twist_to_ackermann.twist_to_ackermann_node:main',
        ],
    },

)
