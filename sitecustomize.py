# This Python file uses the following encoding: utf-8
# @author runhey
# github https://github.com/runhey
"""
Python 解释器全局自动挂载钩子 (Sitecustomize)
无论通过 OASX GUI、命令行 pyonmyoji.py 还是 script.py 启动，
Python 解释器均会在第一时间自动装载 user_tasks/ 下的所有自定义插件，
对主仓库所有核心文件保持 100% 零修改。
"""
import sys
from pathlib import Path

project_root = Path(__file__).parent.resolve()
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

try:
    import user_tasks.plugin_hook
except Exception:
    pass
