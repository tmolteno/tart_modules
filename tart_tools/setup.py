from setuptools import setup

with open('README.md') as f:
    readme = f.read()

setup(
    name='tart_tools',
    version='1.3.1',
    description='Transient Array Radio Telescope Command Line Tools',
    long_description=readme,
    long_description_content_type="text/markdown",
    url='http://github.com/tmolteno/tart_modules',
    author='Tim Molteno',
    author_email='tim@elec.ac.nz',
    license='GPLv3',
    install_requires=['numpy', 'tart',
                      'requests', 'tqdm', 'minio'],
    packages=['tart_tools'],
    scripts=['bin/tart_image',
             'bin/tart_calibrate',
             'bin/tart_calibration_data',
             'bin/tart_vis2json',
             'bin/tart_download_gains',
             'bin/tart_upload_gains',
             'bin/tart_download_data',
             'bin/tart_get_archive_data',
             'bin/tart_set_mode',
             'bin/tart_download_antenna_positions',
             'bin/tart_upload_antenna_positions'],
    classifiers=[
        "Development Status :: 4 - Beta",
        "Topic :: Scientific/Engineering",
        "Topic :: Communications :: Ham Radio",
        "License :: OSI Approved :: GNU General Public License v3 (GPLv3)",
        'Programming Language :: Python :: 3',
        "Intended Audience :: Science/Research"])
