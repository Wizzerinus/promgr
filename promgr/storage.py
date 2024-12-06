import pathlib
import subprocess
import dataclasses
import re
import os
import shutil

from promgr.cache import load_cache, ProjectCache
from promgr.config import Config, read_config


@dataclasses.dataclass
class ProjectMgrData:
    config: Config
    cache: ProjectCache

    categories: set[str] = dataclasses.field(init=False)

    cleanup_regex = re.compile("[^-a-zA-Z0-9_/]+")

    def __post_init__(self):
        self.categories = {p.name for p in self.cache.projects.values() if p.category == "template"}
        self.categories.add("template")

    def clean(self, name: str) -> str:
        name_clean = name.lower().replace(" ", "_")
        return self.cleanup_regex.sub("", name_clean)

    def gen_path(self, category: str, name: str) -> pathlib.Path | None:
        name = self.clean(name)
        category = self.clean(category)
        if not name or not category:
            return None
        if category == "template":
            return pathlib.Path(self.config.paths.templates) / name
        return pathlib.Path(self.config.paths.work) / category / name

    def gen_cat_path(self, category: str) -> pathlib.Path:
        category = self.clean(category)
        return pathlib.Path(self.config.paths.templates) / category

    def create_template(self, name: str) -> bool:
        if self.create_project("template", name):
            self.categories.add(name)
            return True
        return False

    def load_template(self, name: str) -> bool:
        path = self.gen_path("template", name)
        if not path or not path.exists():
            return False
        self._load_project(path, "template", name)
        return True

    def copy_template(self, old_name: str, new_name: str) -> bool:
        path = self.gen_path("template", new_name)
        old_path = self.gen_path("template", old_name)
        if not path or path.exists() or not old_path or not old_path.exists():
            return False
        self.cache.add(path, new_name, "template")
        self.categories.add(new_name)
        self._clone_project(old_path, path)
        self._load_project(path, "template", new_name)
        return True

    def create_project(self, category: str, name: str) -> bool:
        path = self.gen_path(category, name)
        if not path or path.exists():
            return False
        path.mkdir(parents=True)
        self.cache.add(path, name, category)
        self._init_project(path, category, name)
        self._load_project(path, category, name)
        return True

    def load_project(self, name: str) -> bool:
        category = self.cache.get_category(name)
        if not category:
            return False
        path = self.cache.get_path(name)
        if not path.exists():
            return False
        self._load_project(path, category, name)
        return True

    def get_categories(self) -> set[str]:
        return self.categories

    def get_projects(self, cat: str) -> list[str]:
        return self.cache.get_projects(cat)

    def remove_project(self, name: str) -> bool:
        if self.cache.remove_project(name):
            self.cache.save()
            return True
        return False

    def remove_template(self, name: str) -> bool:
        if self.cache.remove_project(name):
            self.categories.discard(name)
            for p in self.cache.get_projects(name):
                self.cache.remove_project(p)
            self.cache.save()
            return True
        return False

    def _init_project(self, path: pathlib.Path, category: str, name: str):
        tpl_folder = self.gen_cat_path(category)
        env = {"TPL": str(tpl_folder), "PROJECT": str(path), "CATEGORY": category, "NAME": name}
        subprocess.Popen([tpl_folder / "create"], env=env)

    def _load_project(self, path: pathlib.Path, category: str, name: str):
        tpl_folder = self.gen_cat_path(category)
        env = {"PM_EDITOR": self.config.apps.editor, "NAME": name}
        subprocess.Popen(
            ["systemd-run", "--user", "--scope", tpl_folder / "launch"],
            env=dict(os.environ, **env),
            start_new_session=True,
            cwd=path,
        )

    def _clone_project(self, old_path: pathlib.Path, new_path: pathlib.Path):
        shutil.copytree(old_path, new_path)


def load_data():
    config = read_config()
    cache = load_cache()
    return ProjectMgrData(config, cache)
