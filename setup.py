from setuptools import setup


with open('LICENSE') as f:
    license = f.read()

setup(
    name='pygogogate2',
    version='0.0.2',
    description='Python package for controlling Gogogate2-Enabled Garage Door',
    author='David Broadfoot',
    author_email='dbroadfoot@gmail.com',
    url='https://github.com/dlbroadfoot/pygogogate2',
    license=license,
    packages=['pygogogate2'],
    package_dir={'pygogogate2': 'pygogogate2'},
    data_files = [('',['LICENSE'])],
    install_requires=[
        'pycryptodomex'
    ]
)
