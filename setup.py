from setuptools import setup

setup(
    name='emergencycontrol',
    version='1.0',
    description='Emergency Control App',
    author='Melopezpe',
    packages=['emergencycontrol'],
    package_dir={'emergencycontrol': '.'},
    package_data={'emergencycontrol': ['EmergencyService.java']},
)
