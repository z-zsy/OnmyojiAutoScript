# This Python file uses the following encoding: utf-8
from user_tasks.MultiAccountDaily.config import MultiAccountDaily

plugin_info = {
    "task_name": "MultiAccountDaily",
    "menu_category": "Daily Task",
    "priority_after": "KekkaiActivationSelf",
    "config_class": MultiAccountDaily,
    "template_config": {
        "scheduler": {
            "enable": False,
            "next_run": "2023-01-01 00:00:00",
            "priority": 2,
            "success_interval": "01 00:00:00",
            "failure_interval": "00 01:00:00",
            "server_update": "17:00:00",
            "delay_date": 1,
            "float_time": "00:00:00"
        },
        "multi_account_daily_config": {
            "enable_gold_youkai": True,
            "enable_experience_youkai": True,
            "enable_daily_trifles": True,
            "sub_account_list": []
        }
    },
    "i18n": {
        "MultiAccountDaily": "小号每日日常",
        "multi_account_daily_config": "小号每日日常配置",
        "enable_gold_youkai": "完成金币妖怪",
        "enable_experience_youkai": "完成经验妖怪",
        "enable_daily_trifles": "完成每日琐事"
    }
}
