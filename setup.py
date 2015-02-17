from setuptools import setup

setup(
    name='jenkinsconnector',
    version='0.1.1',
    description='A library to communicate with jenkins',
    url='https://github.com/AxiaCore/jenkins-connector',
    author='AxiaCore',
    author_email='info@axiacore.com',
    license='MIT',
    packages=['jenkinsconnector'],
    install_requires=['pyquery'],
    zip_safe=False,
)
