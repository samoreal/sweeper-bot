from setuptools import setup, find_packages

setup (
    name = 'SweeperBot',
    version = '0.2',
    package_dir = { '' : 'app' },
    packages = find_packages('app'),
    scripts = ['app/sweeperbot.py'],
    package_data = {
        "sweeperbot" : [ "createtables.sql" ]
    },
    install_requires = [
        'requests'
    ],
    entry_points = {
        'console_scripts' : [ 'sweeperbot = sweeperbot:main' ]
    }
)
