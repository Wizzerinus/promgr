import logging

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
        self.subscribe(KeywordQueryEvent, KeywordQueryEventListener())
        self.subscribe(ItemEnterEvent, ItemEnterEventListener())


class ItemEnterEventListener(EventListener):
    def __init__(self):
        self.action_callbacks = {
            "cp": self.create_project,
            "op": self.open_project,
            "ct": self.create_template,
            "ot": self.open_template,
        }

    def create_project(self, data, category_name, project_name):
        data.create_project(category_name, project_name)

    def open_project(self, data, name):
        data.load_project(name)

    def create_template(self, data, name):
        data.create_template(name)

    def open_template(self, data, name):
        data.load_template(name)
        
    def on_event(self, event, extension: ULauncherExtension):
        action, *args = event.get_data()
        logging.info("processing event: %s(%s)", action, args)
        self.action_callbacks[action](extension.data, *args)
        

class KeywordQueryEventListener(EventListener):
    def __init__(self):
        self.keyword = "pro"
        self.action_callbacks = {
            "c": self.create_project,
            "o": self.open_project,
            "t": self.create_template,
            "m": self.modify_template
        }

    def create_project(self, text, data):
        if " " in text:
            category, name = text.split(" ", 1)
            category = category.strip()
            name = name.strip()
        else:
            category = ""
            name = text.strip()

        cats = data.get_categories()
        if category == "":
            name = name.lower()
            return [
                ExtensionResultItem(
                    icon="images/create.png",
                    name=cat,
                    on_enter=SetUserQueryAction(f"{self.keyword} c {cat} ")
                )
                for cat in sorted(cats)
                if name in cat.lower()
            ]
        if category not in cats:
            return []
        return [
            ExtensionResultItem(
                icon="images/create.png",
                name="Enter the project name",
                on_enter=ExtensionCustomAction(data=["cp", category, name])
            )
        ]

    def open_project(self, text, data):
        if " " in text:
            category, name = text.split(" ", 1)
            category = category.strip()
            name = name.strip()
        else:
            category = ""  # select category first
            name = text.strip()

        name = name.lower()
        if not category:
            cats = data.get_categories()
            return [
                ExtensionResultItem(
                    icon="images/open.png",
                    name=cat,
                    on_enter=SetUserQueryAction(f"{self.keyword} o {cat} ")
                )
                for cat in cats
                if name in cat.lower()
            ]
        projs = data.get_projects(category)
        return [
            ExtensionResultItem(
                icon="images/open.png",
                name=pn,
                on_enter=ExtensionCustomAction(data=["op", pn])
            )
            for pn in projs
            if name in pn.lower()
        ]

    def create_template(self, text, data):
        return [
            ExtensionResultItem(
                icon="images/new-template.png",
                name="Enter the template name",
                on_enter=ExtensionCustomAction(data=["ct", text])
            )
        ]

    def modify_template(self, text, data):
        cats = data.get_categories()
        text = text.lower()
        return [
            ExtensionResultItem(
                icon="images/template.png",
                name=cat,
                on_enter=ExtensionCustomAction(data=["ot", cat])
            )
            for cat in cats
            if text in cat.lower()
        ]

    def get_default_options(self):
        return [
            ExtensionResultItem(
                icon="images/create.png",
                name="Create a project",
                on_enter=SetUserQueryAction(f"{self.keyword} c ")
            ),
            ExtensionResultItem(
                icon="images/open.png",
                name="Open a project",
                on_enter=SetUserQueryAction(f"{self.keyword} o ")
            ),
            ExtensionResultItem(
                icon="images/new-template.png",
                name="Create a template",
                on_enter=SetUserQueryAction(f"{self.keyword} t ")
            ),
            ExtensionResultItem(
                icon="images/template.png",
                name="Open a template",
                on_enter=SetUserQueryAction(f"{self.keyword} m ")
            ),
        ]
    
    def on_event(self, event, extension: ULauncherExtension):
        query = str(event.query)
        if " " in query:
            keyword = query.split(" ", 1)[1]
        else:
            keyword = ""

        if " " not in keyword:
            items = self.get_default_options()
        else:
            action, data = keyword.split(" ", 1)
            action = action.strip().lower()[:1]
            if action not in self.action_callbacks:
                items = self.get_default_options()
            else:
                items = self.action_callbacks[action](data, extension.data)
        
        return RenderResultListAction(items)
