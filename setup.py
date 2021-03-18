"""
setup.py for pyfgc.

For reference see
https://packaging.python.org/guides/distributing-packages-using-setuptools/

"""
from pathlib import Path
from setuptools import setup, find_packages


HERE = Path(__file__).parent.absolute()
with (HERE / 'README.md').open('rt') as fh:
    LONG_DESCRIPTION = fh.read().strip()


REQUIREMENTS: dict = {
    'core': [
        'pyfgc_decoders>=0.0.3',
        'pyfgc_rbac>=1.1',
        'pyfgc_name>=1.3.1',
        'pyserial>=3.4',
# 'mandatory-requirement1',
        # 'mandatory-requirement2',
    ],
    'test': [
        'pytest',
        'hypothesis',
    ],
    'dev': [
        # 'requirement-for-development-purposes-only',
    ],
    'doc': [
        'sphinx',
        'acc_py_sphinx',
    ],
}


setup(
    name='pyfgc',
    version="1.4.1",

    author='Carlos Ghabrous Larrea, Nuno Laurentino Mendes, Joao Afonso',
    author_email='carlos.ghabrous@cern.ch, nuno.laurentino.mendes@cern.ch, joao.afonso@cern.ch',
    description='FGC communication library',
    long_description=LONG_DESCRIPTION,
    long_description_content_type='text/markdown',
    url='',

    packages=find_packages(),
    python_requires='>=3.6, <4',
    classifiers=[
        "Programming Language :: Python :: 3",
        "Operating System :: OS Independent",
    ],

    install_requires=REQUIREMENTS['core'],
    extras_require={
        **REQUIREMENTS,
        # The 'dev' extra is the union of 'test' and 'doc', with an option
        # to have explicit development dependencies listed.
        'dev': [req
                for extra in ['dev', 'test', 'doc']
                for req in REQUIREMENTS.get(extra, [])],
        # The 'all' extra is the union of all requirements.
        'all': [req for reqs in REQUIREMENTS.values() for req in reqs],
    },
)
