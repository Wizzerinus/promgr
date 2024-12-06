import dataclasses
import pathlib
import json


CachePath = pathlib.Path("~/.cache/promgr_prcache.json").expanduser()


@dataclasses.dataclass
class ProjectData:
    path: str
    name: str
    category: str


@dataclasses.dataclass
class ProjectCache:
    projects: dict[str, ProjectData] = dataclasses.field(default_factory=dict)
    backups: dict[str, ProjectData] = dataclasses.field(default_factory=dict)

    def __post_init__(self):
        for p, d in self.projects.items():
            if isinstance(d, dict):
                self.projects[p] = ProjectData(**d)

    def add(self, path: pathlib.Path, name: str, category: str):
        pd = ProjectData(str(path), name, category)
        self.projects[name] = pd
        save_cache(self)

    def get_category(self, name: str):
        if name not in self.projects:
            return None
        return self.projects[name].category

    def get_path(self, name: str):
        if name not in self.projects:
            return None
        return pathlib.Path(self.projects[name].path)

    def get_projects(self, category: str):
        if category == "":
            return [p.name for p in self.projects.values()]

        return [p.name for p in self.projects.values() if p.category == category]

    def remove_project(self, name: str):
        if name not in self.projects:
            return False
        self.backups[name] = self.projects[name]
        del self.projects[name]

    def save(self):
        save_cache(self)


def load_cache() -> ProjectCache:
    if CachePath.exists():
        with open(CachePath) as f:
            data = json.load(f)
    else:
        data = {}
    return ProjectCache(**data)


def save_cache(pc: ProjectCache):
    CachePath.parent.mkdir(exist_ok=True)
    with open(CachePath, "w") as f:
        json.dump(dataclasses.asdict(pc), f)
