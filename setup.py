from setuptools import setup, find_packages

# read the contents of your README file
from os import path
this_directory = path.abspath(path.dirname(__file__))
with open(path.join(this_directory, 'README.rst'), encoding='utf-8') as f:
    long_description = f.read()

setup(
    name='irgen',
    version='0.1.2',
    description='A python tool for generating and converting ir formats',
    long_description=long_description,
    long_description_content_type='text/x-rst',
    license='MIT',
    packages=find_packages('src'),
    package_dir = {'': 'src'},
    python_requires='>3.5',
    author='Joakim Plate',
    install_requires=[
        'asyncio',
        'requests'
    ],
    extras_require={
        'tests': [
            'pytest>3.6.4',
            'pytest-cov<2.6',
            'coveralls'
        ]
    },
    entry_points = {
        'console_scripts' : ['irgen=irgen.__main__:main']
    },
    url='https://github.com/elupus/irgen',
    classifiers=[
        'License :: OSI Approved :: MIT License',
        'Development Status :: 4 - Beta',
        'Environment :: Console',
        'Environment :: Plugins',
    ]
)
