import setuptools

setuptools.setup(
	name='sis2calgroups',
	version='0.1',
	description='Creates and populates CalGroups from SIS data.',
	url='https://github.com/ryanlovett/sis2calgroups',
	author='Ryan Lovett',
	author_email='rylo@berkeley.edu',
	packages=setuptools.find_packages(),
	install_requires=[
	  'requests'
	],
    entry_points={
        'console_scripts': [
            'sis2calgroups = sis2calgroups.__main__:main',
        ],
    },

)
