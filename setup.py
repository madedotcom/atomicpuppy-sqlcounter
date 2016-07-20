from setuptools import setup, find_packages

install_requires = [
#    "atomicpuppy==0.3.0",
    "retrying==1.3.3",
]

tests_require = [
    "Contexts==0.10.2",
]

setup(
    name="AtomicPuppy-SqlCounter",
    version="0.0.1",
    install_requires=install_requires,
    tests_require=tests_require,
    py_modules=['atomicpuppy_sqlcounter'],
    url='https://github.com/madedotcom/atomicpuppy/contribs/sqlcounter',
    description='A sqlalchemy based counter for AtomicPuppy',
    author='Francesco Pighi',
    keywords=['AtomicPuppy'],
    license='MIT',
)
