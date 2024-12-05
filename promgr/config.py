import dataclasses
import tomllib
import pathlib
import logging


@dataclasses.dataclass
class PathConfig:
    templates: str
    work: str


@dataclasses.dataclass
class AppConfig:
    editor: str


@dataclasses.dataclass
class Config:
    paths: PathConfig
    apps: AppConfig

    def __post_init__(self):
        if isinstance(self.paths, dict):
            self.paths = PathConfig(**self.paths)
        if isinstance(self.apps, dict):
            self.apps = AppConfig(**self.apps)


def merge_dicts_recursive(target: dict, overrides: dict):
    for k, v in overrides.items():
        if isinstance(v, dict):
            if k not in target:
                target[k] = {}
            merge_dicts_recursive(target[k], v)
        else:
            target[k] = v


def read_config() -> Config:
    files = [
        pathlib.Path("/usr/share/promgr/promgr.toml"),
        pathlib.Path("~/.local/share/ulauncher/extensions/com.github.wizzerinus.promgr/promgr.toml").expanduser(),
        pathlib.Path("~/.local/share/promgr/promgr.toml").expanduser(),
        pathlib.Path("~/.config/promgr.toml").expanduser(),
    ]

    target = {}
    for f in files:
        if f.exists():
            logging.info(f"opening setting file: {f}")
            with open(f, "rb") as fd:
                data = tomllib.load(fd)
            merge_dicts_recursive(target, data)

    return Config(**target)
