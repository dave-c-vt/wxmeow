from setuptools import setup

setup(
    name='meowcast',
    packages=['meowcast'],
    version='0.1.0',
    include_package_data=True,
    install_requires=[
        'flask',
        'flask_wtf',
        'requests',
        'wtforms',
    ],
)
