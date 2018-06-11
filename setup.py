from setuptools import setup


install_requires = [
    "atomicpuppy",
    "retrying",
]

setup(
    name="atomicpuppy_sqlcounter",
    version="0.21",
    install_requires=install_requires,
    py_modules=['atomicpuppy_sqlcounter'],
    url='https://github.com/madedotcom/atomicpuppy-sqlcounter',
    description='A sqlalchemy based counter for AtomicPuppy',
    author='Francesco Pighi',
    author_email='tech@made.com',
    keywords=['AtomicPuppy'],
    download_url='https://github.com/madedotcom/atomicpuppy-sqlcounter/tarball/0.1rc3',
    license='MIT',
)
