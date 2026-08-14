# This Python file uses the following encoding: utf-8
# @author runhey
# github https://github.com/runhey
import os
import sys
import importlib
from pathlib import Path
from pydantic import Field

from module.logger import logger

_PLUGINS_LOADED = False


def load_custom_plugins():
    global _PLUGINS_LOADED
    if _PLUGINS_LOADED:
        return
    _PLUGINS_LOADED = True

    project_root = Path(__file__).parent.parent.resolve()
    user_tasks_dir = project_root / "user_tasks"

    if not user_tasks_dir.exists():
        user_tasks_dir.mkdir(parents=True, exist_ok=True)
        return

    if str(project_root) not in sys.path:
        sys.path.insert(0, str(project_root))

    plugin_folders = [d for d in user_tasks_dir.iterdir() if d.is_dir() and (d / "plugin.py").exists()]

    if not plugin_folders:
        logger.info("[PluginLoader] No custom plugins found in user_tasks/")
        return

    for plugin_dir in plugin_folders:
        folder_name = plugin_dir.name
        try:
            mod_path = f"user_tasks.{folder_name}.plugin"
            plugin_module = importlib.import_module(mod_path)
            plugin_info = getattr(plugin_module, "plugin_info", None)
            if not plugin_info:
                logger.warning(f"[PluginLoader] Plugin {folder_name} missing plugin_info dictionary")
                continue

            _register_plugin(plugin_info)
            logger.info(f"[PluginLoader] Successfully loaded custom plugin: {plugin_info.get('task_name', folder_name)}")
        except Exception as e:
            logger.error(f"[PluginLoader] Failed to load custom plugin {folder_name}: {e}")


def _register_plugin(info: dict):
    task_name = info["task_name"]
    menu_category = info.get("menu_category", "Daily Task")
    priority_after = info.get("priority_after")
    config_class = info.get("config_class")
    template_config = info.get("template_config", {})
    i18n_dict = info.get("i18n", {})

    from module.config.utils import convert_to_underscore
    field_name = convert_to_underscore(task_name)

    # 1. 动态注入 ConfigModel 属性 (支持 Pydantic v2)
    if config_class:
        from module.config.config_model import ConfigModel
        from pydantic.fields import FieldInfo
        if field_name not in ConfigModel.model_fields:
            field_info = FieldInfo.from_annotated_attribute(config_class, config_class())
            ConfigModel.model_fields[field_name] = field_info
            ConfigModel.__annotations__[field_name] = config_class
            try:
                ConfigModel.model_rebuild(force=True)
            except Exception as e:
                logger.warning(f"[PluginLoader] model_rebuild warning: {e}")

    # 2. 动态注入 ConfigMenu 菜单
    from module.config.config_menu import ConfigMenu
    if not getattr(ConfigMenu, "_plugin_hooked", False):
        orig_init = ConfigMenu.__init__
        _registered_menu_items = []

        def new_init(self):
            orig_init(self)
            for item in _registered_menu_items:
                cat, name = item["category"], item["name"]
                if cat in self.menu and name not in self.menu[cat]:
                    self.menu[cat].append(name)

        ConfigMenu.__init__ = new_init
        ConfigMenu._registered_menu_items = _registered_menu_items
        ConfigMenu._plugin_hooked = True

    ConfigMenu._registered_menu_items.append({"category": menu_category, "name": task_name})

    # 3. 动态注入 ConfigManual 调度优先级
    if priority_after:
        from module.config.config_manual import ConfigManual
        if task_name not in ConfigManual.SCHEDULER_PRIORITY:
            ConfigManual.SCHEDULER_PRIORITY = ConfigManual.SCHEDULER_PRIORITY.replace(
                priority_after, f"{priority_after} > {task_name}"
            )

    # 4. 动态注入 template.json 默认配置
    if template_config:
        from module.config.config_model import ConfigModel
        orig_read_json = ConfigModel.read_json

        if not getattr(ConfigModel, "_template_plugin_hooked", False):
            _registered_templates = {}

            def patched_read_json(config_name: str) -> dict:
                data = orig_read_json(config_name)
                for k, v in _registered_templates.items():
                    if k not in data:
                        data[k] = v
                return data

            ConfigModel.read_json = staticmethod(patched_read_json)
            ConfigModel._registered_templates = _registered_templates
            ConfigModel._template_plugin_hooked = True

        ConfigModel._registered_templates[field_name] = template_config

    # 5. 动态注入 i18n 翻译字典
    if i18n_dict:
        try:
            from assets.i18n.i18n import i18n
            if hasattr(i18n, "translations") and isinstance(i18n.translations, dict):
                i18n.translations.update(i18n_dict)
        except Exception:
            pass
