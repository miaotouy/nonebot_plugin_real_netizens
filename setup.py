from setuptools import find_packages, setup

setup(
    name='nonebot_plugin_real_netizens',
    version='0.1.0',
    packages=find_packages(),
    author='miaotouy',  # 这里请填写你的姓名
    author_email='pngbige@163.com',  # 这里请填写你的邮箱地址
    description='AI虚拟群友插件 for Nonebot2',
    long_description=open('README.md', 'r', encoding='utf-8').read(),
    long_description_content_type="text/markdown",
    url='{https://github.com/miaotouy/nonebot_plugin_real_netizens}',  # 这里请填写你的插件项目的地址，例如：GitHub 仓库地址
    license='MIT License',
    install_requires=[
        'sqlalchemy>=1.4.0',
        'pydantic>=1.8.0',
        'PyYAML>=6.0',
        'aiohttp>=3.8.0',
        'nonebot2>=2.0.0',
        'nonebot-adapter-onebot>=2.0.0',
        'nonebot-plugin-datastore>=0.1.0',
        'nonebot-plugin-txt2img>=0.3.0',
        'nonebot-plugin-apscheduler>=0.2.0',
        'nonebot-plugin-userinfo>=0.1.0'
        # 添加其他依赖，并指定版本号范围
    ],
    classifiers=[
        'Development Status :: 4 - Beta',
        'Intended Audience :: Developers',
        'License :: OSI Approved :: MIT License',
        'Programming Language :: Python :: 3.8',
        'Programming Language :: Python :: 3.9',
        'Programming Language :: Python :: 3.10',
        'Programming Language :: Python :: 3.11',
        'Operating System :: OS Independent',
        'Framework :: Robot Framework :: Library',
        'Topic :: Software Development :: Libraries :: Python Modules'
    ],
    entry_points={
        'nonebot.plugins': [
            'nonebot_plugin_real_netizens = nonebot_plugin_real_netizens'
        ]
    }
)
