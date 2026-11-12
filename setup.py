from setuptools import setup

setup(
    name='emergencycontrol',
    version='1.0',
    description='Emergency Control App',
    packages=['emergencycontrol'],
    package_dir={'emergencycontrol': 'src/main/java/org/phonecontrol/emergencycontrol'},
    package_data={'emergencycontrol': ['*.java']},
)
