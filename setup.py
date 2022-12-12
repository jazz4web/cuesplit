from setuptools import setup, find_packages

from cuesplit import version

DESCRIPTION = """
This is a simple tool for reading cuesheet files,
splitting CDDA-images to tracks and filling tracks' metadata
""".replace('\n', ' ').strip()


setup(
    name='cuesplit',
    version=version,
    packages=find_packages(),
    python_requires='~=3.8',
    install_requires=['chardet>=3.0.4'],
    zip_safe=False,
    scripts=['bin/cuesplit'],
    author='AndreyVM',
    author_email='webmaster@codej.ru',
    description=DESCRIPTION,
    license='GNU GPLv3',
    keywords='cue cdda flac mp3 opus vorbis cdda-image-splitter',
    url='https://githum.com/newbie-c/cuesplit')
