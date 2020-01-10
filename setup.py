from setuptools import setup

with open('README.md') as f:
    long_description = f.read()

setup(
    name='dbxlogger',
    version='0.0.1',
    description='A simple package for structured experiment logs',
    long_description=long_description,
    long_description_content_type='text/markdown',
    url='http://github.com/vladvelici/dbxlogger',
    author='Vlad Velici',
    author_email='vlad.velici@gmail.com',
    license='MIT',
    packages=['dbxlogger'],
)
