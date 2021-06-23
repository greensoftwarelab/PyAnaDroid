import setuptools
from setuptools import setup
#from manafa._version import __version__

with open("README.md", "r", encoding='utf-8') as fh:
    long_description = fh.read()

with open('requirements.txt') as f:
    required = f.read().splitlines()


setup(
    name='anadroid',
    description='Anadroid: Energy benchmarking/analyzer tool for Android',
    long_description=long_description,
    long_description_content_type='text/markdown',
    author='Rui Rua',
    author_email='rui.rrua@gmail.com',
    url='https://github.com/RRua/pyAnaDroid',
    license='MIT',
    packages=setuptools.find_packages(),
    use_incremental=True,
    install_requires=required, #TODO replace this by minimal config
    setup_requires=['incremental'],
    include_package_data=True,
    classifiers=[
        'License :: OSI Approved :: MIT License',
        'Intended Audience :: Science/Research',
        'Operating System :: POSIX',
        'Programming Language :: Python :: 3.8',
    ],
    project_urls={
        'Bug Tracker':  'https://github.com/RRua/pyAnaDroid/issues'
        },
    python_requires=">=3.8",
)
