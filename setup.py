from setuptools import setup, find_packages

setup(
    name='irgen',
    version='0.1.0',
    description='A python tool for generating and converting ir formats',
    license='MIT',
    packages=find_packages('src'),
    package_dir = {'': 'src'},
    python_requires='>3.5',
    author='Joakim Plate',
    install_requires=[],
    extras_require={
        'tests': []
    },
    entry_points = {
        'console_scripts' : ['irgen=irgen.console:main']
    },
    url='https://github.com/elupus/irgen',
    classifiers=[
        'License :: OSI Approved :: MIT License',
        'Development Status :: 4 - Beta',
        'Environment :: Console',
        'Environment :: Plugins',
    ]
)
