import logging
import dataclasses
from typing import Callable

from ulauncher.api.client.Extension import Extension
from ulauncher.api.client.EventListener import EventListener
from ulauncher.api.shared.event import KeywordQueryEvent, ItemEnterEvent
from ulauncher.api.shared.item.ExtensionResultItem import ExtensionResultItem
from ulauncher.api.shared.action.RenderResultListAction import RenderResultListAction
from ulauncher.api.shared.action.SetUserQueryAction import SetUserQueryAction
from ulauncher.api.shared.action.ExtensionCustomAction import ExtensionCustomAction

from promgr.storage import ProjectMgrData, load_data


class ULauncherExtension(Extension):
    data: ProjectMgrData

    def __init__(self):
        super().__init__()
        self.data = load_data()
        self.subscribe(KeywordQueryEvent, KeywordQueryEventListener(self.data))
        self.subscribe(ItemEnterEvent, ItemEnterEventListener(self.data))


class ItemEnterEventListener(EventListener):
    data: ProjectMgrData

    def __init__(self, data):
        self.data = data
        self.action_callbacks = {
            "cp": self.create_project,
            "op": self.open_project,
            "rp": self.remove_project,
            "ct": self.create_template,
            "dt": self.copy_template,
            "ot": self.open_template,
            "rt": self.remove_template,
        }

    def create_project(self, category_name: str, project_name: str):
        self.data.create_project(category_name, project_name)

    def open_project(self, name: str):
        self.data.load_project(name)

    def remove_project(self, name: str):
        self.data.remove_project(name)

    def create_template(self, name: str):
        self.data.create_template(name)

    def copy_template(self, old_name: str, new_name: str):
        self.data.copy_template(old_name, new_name)

    def open_template(self, name: str):
        self.data.load_template(name)

    def remove_template(self, name: str):
        self.data.remove_template(name)

    def on_event(self, event, extension: ULauncherExtension):
        action, *args = event.get_data()
        logging.info("processing event: %s(%s)", action, args)
        self.action_callbacks[action](*args)


@dataclasses.dataclass
class ProjectData:
    callback: Callable[[str], list[ExtensionResultItem]]
    name: str
    icon: str


class KeywordQueryEventListener(EventListener):
    data: ProjectMgrData

    def __init__(self, data):
        self.data = data
        self.keyword = "pro"
        self.action_callbacks = {
            "new": ProjectData(self.create_project, "Create a project", "create-project.png"),
            "open": ProjectData(self.open_project, "Open a project", "open-project.png"),
            "tmp-new": ProjectData(self.create_template, "Create a template", "create-template.png"),
            "tmp-open": ProjectData(self.modify_template, "Modify a template", "open-template.png"),
            "tmp-copy": ProjectData(self.copy_template, "Copy a template", "copy-template.png"),
            "rm": ProjectData(self.remove_project, "Remove a project", "remove-project.png"),
            "tmp-rm": ProjectData(self.remove_template, "Remove a template", "remove-template.png"),
        }

    def create_project(self, text: str):
        if " " in text:
            category, name = text.split(" ", 1)
            category = category.strip()
            name = name.strip()
        else:
            category = ""
            name = text.strip()

        cats = self.data.get_categories()
        if category == "":
            name = name.lower()
            return [
                ExtensionResultItem(
                    icon="images/create-project.png", name=cat, on_enter=SetUserQueryAction(f"{self.keyword} c {cat} ")
                )
                for cat in sorted(cats)
                if name in cat.lower()
            ]
        if category not in cats:
            return []
        return [
            ExtensionResultItem(
                icon="images/create-project.png",
                name="Enter the project name",
                on_enter=ExtensionCustomAction(data=["cp", category, name]),
            )
        ]

    def open_project(self, text: str):
        if " " in text:
            category, name = text.split(" ", 1)
            category = category.strip()
            name = name.strip()
        else:
            category = None  # select category first
            name = text.strip()

        name = name.lower()
        if category is None:
            cats = self.data.get_categories()
            return [
                ExtensionResultItem(
                    icon="images/open-project.png", name=cat, on_enter=SetUserQueryAction(f"{self.keyword} o {cat} ")
                )
                for cat in cats
                if name in cat.lower()
            ]
        projs = self.data.get_projects(category)
        return [
            ExtensionResultItem(icon="images/icon.png", name=pn, on_enter=ExtensionCustomAction(data=["op", pn]))
            for pn in projs
            if name in pn.lower()
        ]

    def remove_project(self, text: str):
        if " " in text:
            category, name = text.split(" ", 1)
            category = category.strip()
            name = name.strip()
        else:
            category = None
            name = text.strip()

        name = name.lower()
        cats = self.data.get_categories()
        if category is None or category not in cats:
            return [
                ExtensionResultItem(
                    icon="images/remove-project.png", name=cat, on_enter=SetUserQueryAction(f"{self.keyword} r {cat} ")
                )
                for cat in cats
                if name in cat.lower()
            ]
        projs = self.data.get_projects(category)
        return [
            ExtensionResultItem(
                icon="images/remove-project.png", name=pn, on_enter=ExtensionCustomAction(data=["rp", pn])
            )
            for pn in projs
            if name in pn.lower()
        ]

    def create_template(self, text: str):
        return [
            ExtensionResultItem(
                icon="images/create-template.png",
                name="Enter the template name",
                on_enter=ExtensionCustomAction(data=["ct", text]),
            )
        ]

    def copy_template(self, text: str):
        if " " in text:
            old_name, new_name = text.split(" ", 1)
            old_name = old_name.strip()
            new_name = new_name.strip()
        else:
            old_name = text.strip()
            new_name = None

        cats = self.data.get_categories()
        if old_name in cats and new_name is not None:
            return [
                ExtensionResultItem(
                    icon="images/copy-template.png",
                    name="Enter the template name",
                    on_enter=ExtensionCustomAction(data=["dt", old_name, new_name]),
                )
            ]
        return [
            ExtensionResultItem(
                icon="images/copy-template.png", name=cat, on_enter=SetUserQueryAction(f"{self.keyword} d {cat} ")
            )
            for cat in cats
            if old_name in cat.lower()
        ]

    def modify_template(self, text: str):
        cats = self.data.get_categories()
        text = text.lower()
        return [
            ExtensionResultItem(
                icon="images/open-template.png", name=cat, on_enter=ExtensionCustomAction(data=["ot", cat])
            )
            for cat in cats
            if text in cat.lower()
        ]

    def remove_template(self, text: str):
        cats = self.data.get_categories()
        text = text.lower()
        return [
            ExtensionResultItem(
                icon="images/remove-template.png", name=cat, on_enter=ExtensionCustomAction(data=["rt", cat])
            )
            for cat in cats
            if text in cat.lower()
        ]

    def get_default_options(self, search: str):
        return [
            ExtensionResultItem(
                icon=f"images/{x.icon}", name=x.name, on_enter=SetUserQueryAction(f"{self.keyword} {k} ")
            )
            for k, x in self.action_callbacks.items()
            if search in k or search in x.name.lower()
        ]

    def on_event(self, event, extension: ULauncherExtension):
        query = str(event.query)
        if " " in query:
            keyword = query.split(" ", 1)[1]
        else:
            keyword = ""

        if " " not in keyword:
            search = keyword.lower()
            items = self.get_default_options(search)
        else:
            action, data = keyword.split(" ", 1)
            action = action.strip().lower()
            if action not in self.action_callbacks:
                items = self.get_default_options(action)
            else:
                items = self.action_callbacks[action].callback(data)

        return RenderResultListAction(items)
