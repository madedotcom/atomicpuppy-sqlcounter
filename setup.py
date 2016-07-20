from setuptools import setup, find_packages

install_requires = [
    "atomicpuppy==0.3rc0",
    "retrying==1.3.3",
]

tests_require = [
    "Contexts==0.10.2",
]

setup(
    name="atomicpuppy_sqlcounter",
    version="0.1rc3",
    install_requires=install_requires,
    tests_require=tests_require,
    py_modules=['atomicpuppy_sqlcounter'],
    url='https://github.com/madedotcom/atomicpuppy-sqlcounter',
    description='A sqlalchemy based counter for AtomicPuppy',
    author='Francesco Pighi',
    keywords=['AtomicPuppy'],
    download_url='https://github.com/madedotcom/atomicpuppy-sqlcounter/tarball/0.1rc3',
    license='MIT',
)
