from setuptools import find_packages, setup

setup(
    name='nonebot_plugin_real_netizens',
    version='0.1.0',
    packages=find_packages(),
    install_requires=[
        'nonebot2>=2.0.0',
        'nonebot-adapter-onebot>=2.0.0',
        'sqlalchemy>=1.4.0',
        'nonebot-plugin-datastore>=0.1.0',
        'pydantic>=1.8.0',
        'PyYAML>=6.0',
        'aiohttp>=3.8.0',
        'nonebot-plugin-txt2img>=0.3.0',
        'nonebot-plugin-apscheduler>=0.2.0',
        'nonebot-plugin-userinfo>=0.1.0',
    ],
    entry_points={
        'nonebot.plugins': [
            'nonebot_plugin_real_netizens = nonebot_plugin_real_netizens'
        ]
    }
)
