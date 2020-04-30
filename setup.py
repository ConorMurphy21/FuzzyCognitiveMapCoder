from setuptools import setup

setup(
    name="FuzzyCogMapDecoder",
    version="1.0",
    description="Tools to help decode fuzzy maps",
    author="Conor Murphy",
    packages=['src'],
    install_requires=[
        'autocorrect'
    ],
    entry_points={
      'console_scripts': [
          'synify = src.synify:main',
          'fcmdecode = src.main:main'
      ]
    }
)
