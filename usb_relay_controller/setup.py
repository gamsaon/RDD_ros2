from glob import glob

from setuptools import find_packages, setup


package_name = 'usb_relay_controller'

setup(
    name=package_name,
    version='0.1.0',
    packages=find_packages(exclude=['test']),
    data_files=[
        ('share/ament_index/resource_index/packages', ['resource/' + package_name]),
        ('share/' + package_name, ['package.xml']),
        ('share/' + package_name + '/launch', glob('launch/*.py')),
        ('share/' + package_name + '/tools', glob('tools/*')),
        ('share/' + package_name + '/udev', glob('udev/*.rules')),
        ('share/' + package_name, ['README.md']),
    ],
    install_requires=['setuptools'],
    zip_safe=True,
    maintainer='zxc',
    maintainer_email='zxc@todo.todo',
    description='ROS2 controller for one or two DCTTech USBRelay4 HID relay modules.',
    license='MIT',
    entry_points={
        'console_scripts': [
            'usb_relay_controller = usb_relay_controller.usb_relay_controller:main',
        ],
    },
)
