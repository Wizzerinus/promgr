import pathlib
import subprocess
import dataclasses
import re
import os

from promgr.cache import load_cache, ProjectCache
from promgr.config import Config, read_config


@dataclasses.dataclass
class ProjectMgrData:
    config: Config
    cache: ProjectCache

    categories: set[str] = None

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
        return self.create_project("template", name)

    def load_template(self, name: str) -> bool:
        path = self.gen_path("template", name)
        if not path.exists():
            return False
        self._load_project(path, "template", name)
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

    def _init_project(self, path, category, name):
        tpl_folder = self.gen_cat_path(category)
        env = {"TPL": str(tpl_folder), "PROJECT": path, "CATEGORY": category, "NAME": name}
        subprocess.Popen([tpl_folder / "create"], env=env)

    def _load_project(self, path, category, name):
        tpl_folder = self.gen_cat_path(category)
        env = {"PM_EDITOR": self.config.apps.editor, "NAME": name}
        subprocess.Popen([tpl_folder / "launch"], env=dict(os.environ, **env), start_new_session=True, cwd=path)


def load_data():
    config = read_config()
    cache = load_cache()
    return ProjectMgrData(config, cache)
