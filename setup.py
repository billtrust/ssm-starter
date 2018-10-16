import re
from setuptools import setup, find_packages


# read the version number from source
version = re.search(
    '^__version__\s*=\s*"(.*)"',
    open('ssm_starter/ssm_starter.py').read(),
    re.M
    ).group(1)

# Get the long description from the relevant file
try:
    # in addition to pip install pypandoc, might have to: apt install -y pandoc
    import pypandoc
    long_description = pypandoc.convert('README.md', 'rst')
except (IOError, ImportError, OSError) as e:
    print("Error converting READMD.md to rst: {}".format(e))
    long_description = open('README.md').read()

setup(name='ssm-starter',
      version=version,
      description='Read AWS SSM parameters into the environment, then start your app.',
      long_description=long_description,
      keywords=['aws', 'ssm', 'aws-ssm', 'parameter-store'],
      author='Doug Kerwin',
      author_email='dwkerwin@gmail.com',
      url='https://github.com/billtrust/ssm-starter',
      install_requires=[
        'boto3>=1.7.20, <2.0',
        'botocore>=1.10.20, <2.0',
        'six>=1.11.0, <2.0'
        ],
      packages=find_packages(exclude=['pypandoc']),
      entry_points={
        "console_scripts": ['ssm-starter = ssm_starter.ssm_starter:main']
        },
      license='MIT',
      classifiers=[
        'Development Status :: 5 - Production/Stable',
        'Intended Audience :: Developers',
        'Natural Language :: English',
        'License :: OSI Approved :: MIT License',
        'Programming Language :: Python',
        'Programming Language :: Python :: 2.7',
        'Programming Language :: Python :: 3',
        'Programming Language :: Python :: 3.3',
        'Programming Language :: Python :: 3.4',
        'Programming Language :: Python :: 3.5',
        'Programming Language :: Python :: 3.6',
        ]
     )
