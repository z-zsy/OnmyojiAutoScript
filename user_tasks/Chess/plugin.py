# This Python file uses the following encoding: utf-8
from user_tasks.Chess.config import Chess

plugin_info = {
    "task_name": "Chess",
    "menu_category": "Weekly Task",
    "priority_after": "Duel",
    "config_class": Chess,
    "template_config": {
        "scheduler": {
            "enable": False,
            "next_run": "2023-01-01 00:00:00",
            "priority": 5,
            "success_interval": "7d",
            "failure_interval": "2h"
        },
        "chess_config": {
            "early_exit": True,
            "remaining_players": 4,
            "run_count": 0,
            "coin_full_exit": True
        }
    },
    "i18n": {
        "Chess": "百鬼棋局",
        "chess_config": "百鬼棋局配置",
        "early_exit": "是否提前退出",
        "early_exit_help": "开启后在存活人数达到设定值时主动退出当前对局",
        "remaining_players": "剩余人数",
        "remaining_players_help": "存活人数小于或等于该数值时主动退出，范围0至8；0表示不退出",
        "run_count": "执行次数",
        "coin_full_exit": "刷满鼬乐币",
        "coin_full_exit_help": "检测到鼬乐币为600/600时结束百鬼棋局"
    }
}
