# tests/check_dependencies.py
import importlib
import sys


def check_dependency(module_name, min_version=None):
    try:
        module = importlib.import_module(module_name)
        if min_version:
            version = getattr(module, '__version__', None)
            if version and version < min_version:
                print(
                    f"Warning: {module_name} version {version} is less than the required version {min_version}")
            elif not version:
                print(
                    f"Warning: Unable to determine version for {module_name}")
        print(f"√ {module_name} is installed")
    except ImportError:
        print(f"X {module_name} is not installed")
        return False
    return True


dependencies = [
    ("sqlalchemy", "1.4.0"),
    ("pydantic", "1.8.0"),
    ("PyYAML", "6.0"),
    ("aiohttp", "3.8.0"),
    ("Pillow", "8.0.0"),
    ("cachetools", "4.2.0"),
    ("imagehash", "4.2.0"),
    ("pytest", "6.2.0"),
    ("pytest_asyncio", "0.14.0"),
    ("pytest_mock", "3.5.0"),
    ("nonebot2", "2.0.0"),
    ("nonebug", "0.2.0"),
    ("nonebot_adapter_onebot", "2.0.0"),
    ("nonebot_plugin_datastore", "0.1.0"),
    ("nonebot_plugin_txt2img", "0.3.0"),
    ("nonebot_plugin_apscheduler", "0.2.0"),
    ("nonebot_plugin_userinfo", "0.1.0"),
    ("nonebot_plugin_localstore", "0.1.0"),
    # ("black", "21.5b1"),
    # ("isort", "5.8.0"),
    # ("flake8", "3.9.2"),
    # ("mypy", "0.812"),
    # ("sphinx", "4.0.2"),
]


def main():
    all_installed = True
    for dep, version in dependencies:
        if not check_dependency(dep, version):
            all_installed = False

    if all_installed:
        print("\nAll dependencies are installed correctly.")
        sys.exit(0)
    else:
        print("\nSome dependencies are missing or have incorrect versions.")
        print("Please install the missing dependencies or update them to the required versions.")
        sys.exit(1)


if __name__ == "__main__":
    main()
