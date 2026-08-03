# This Python file uses the following encoding: utf-8
from user_tasks.DokanSelf.config import DokanSelf

plugin_info = {
    "task_name": "DokanSelf",
    "menu_category": "Daily Task",
    "priority_after": "Dokan",
    "config_class": DokanSelf,
    "template_config": {
        "scheduler": {
            "enable": False,
            "next_run": "2023-01-01 00:00:00",
            "priority": 3,
            "success_interval": "01 00:00:00",
            "failure_interval": "00 02:00:00",
            "server_update": "20:00:00",
            "delay_date": 1,
            "float_time": "00:00:00"
        },
        "dokan_config": {
            "only_attack_target_icon": True,
            "fallback_random_if_not_found": False,
            "find_dokan_refresh_count": 7,
            "find_dokan_score": 4.6,
            "min_people_num": -1,
            "min_bounty": 0,
            "monday_to_thursday": True,
            "try_start_dokan": False
        }
    },
    "i18n": {
        "DokanSelf": "道馆突破-鑫",
        "dokan_self_config": "道馆突破-鑫配置",
        "only_attack_target_icon": "只打【鑫】字道馆",
        "only_attack_target_icon_help": "开启后，只挑战带【鑫】字寮徽标志的道馆，其他道馆自动跳过",
        "fallback_random_if_not_found": "刷完后保底打其他道馆",
        "fallback_random_if_not_found_help": "默认关闭。开启后，若设定的刷新上限用完仍未找到【鑫】字道馆，则保底挑战一个随机道馆"
    }
}
