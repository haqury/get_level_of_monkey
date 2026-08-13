"""Build standalone Windows release with Panda3D build_apps."""

from setuptools import setup

APP_NAME = "get_level_of_monkey"

setup(
    name=APP_NAME,
    version="0.2.0",
    options={
        "build_apps": {
            "gui_apps": {
                APP_NAME: "main.py",
            },
            "log_filename": f"$USER_APPDATA/{APP_NAME}/output.log",
            "log_append": False,
            "requirements_path": "./requirements-release.txt",
            "platforms": ["win_amd64"],
            "include_patterns": [
                "assets/**/*.png",
                "assets/fonts/*.ttf",
                "config/*.json",
                "config/locale/*.json",
            ],
            "plugins": [
                "pandagl",
                "p3openal_audio",
            ],
            "include_modules": {
                "*": [
                    "multiprocessing",
                    "multiprocessing.shared_memory",
                ],
            },
        }
    },
)
