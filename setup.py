import setuptools

setuptools.setup(
    name='daoagent',
    version='0.1.1',
    packages=setuptools.find_packages(),
    install_requires=['pyzmq', 'python-daemon >= 1.5.0', 'sh'],
    entry_points={
        'console_scripts':
            ['dao-agent = daoagent.run_manager:run']})
