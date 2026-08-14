# This Python file uses the following encoding: utf-8
# @author runhey
# github https://github.com/runhey
import sys
import importlib
import importlib.abc
import importlib.util
from pathlib import Path

project_root = Path(__file__).parent.parent.resolve()
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))


class CustomPluginImportHook(importlib.abc.MetaPathFinder):
    """
    全局 Python 导入拦截钩子：
    1. 当导入 module.config / script 模块时，自动触发注册 user_tasks/ 下的所有插件。
    2. 当尝试导入 tasks.<CustomTask> 且 tasks/ 下不存在时，动态重定向到 user_tasks.<CustomTask>
    """
    _hook_installed = False

    @classmethod
    def install(cls):
        if not cls._hook_installed:
            sys.meta_path.insert(0, cls())
            cls._hook_installed = True

    def find_spec(self, fullname, path, target=None):
        if fullname.startswith("module.config") or fullname == "script":
            try:
                from user_tasks.plugin_loader import load_custom_plugins
                load_custom_plugins()
            except Exception:
                pass

        if fullname.startswith("tasks."):
            parts = fullname.split(".")
            if len(parts) >= 2:
                task_name = parts[1]
                task_dir = project_root / "tasks" / task_name
                user_task_dir = project_root / "user_tasks" / task_name

                if not task_dir.exists() and user_task_dir.exists():
                    user_fullname = "user_tasks." + ".".join(parts[1:])
                    try:
                        spec = importlib.util.find_spec(user_fullname)
                        if spec:
                            return spec
                    except Exception:
                        pass
        return None


CustomPluginImportHook.install()

try:
    from user_tasks.plugin_loader import load_custom_plugins
    load_custom_plugins()
except Exception:
    pass
