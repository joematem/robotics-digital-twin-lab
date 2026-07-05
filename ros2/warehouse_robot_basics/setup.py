from setuptools import find_packages, setup

package_name = 'warehouse_robot_basics'

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
    maintainer='joematem',
    maintainer_email='joematem@gmail.com',
    description='TODO: Package description',
    license='TODO: License declaration',
    extras_require={
        'test': [
            'pytest',
        ],
    },
    entry_points={
    'console_scripts': [
        'robot_status_publisher = warehouse_robot_basics.robot_status_publisher:main',
        'robot_status_subscriber = warehouse_robot_basics.robot_status_subscriber:main',
        'robot_status_db_logger = warehouse_robot_basics.robot_status_db_logger:main',
    ],
},
)
