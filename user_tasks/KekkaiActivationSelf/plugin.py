# This Python file uses the following encoding: utf-8
from user_tasks.KekkaiActivationSelf.config import KekkaiActivationSelf

plugin_info = {
    "task_name": "KekkaiActivationSelf",
    "menu_category": "Daily Task",
    "priority_after": "KekkaiActivation",
    "config_class": KekkaiActivationSelf,
    "template_config": {
        "scheduler": {
            "enable": False,
            "next_run": "2023-01-01 00:00:00",
            "priority": 2,
            "success_interval": "01 00:00:00",
            "failure_interval": "00 10:00:00",
            "server_update": "09:00:00",
            "delay_date": 1,
            "float_time": "00:00:00"
        },
        "activation_config": {
            "card_type": "太鼓",
            "star_priority": "6>5>4>3",
            "min_taiko_num": 8,
            "min_fish_num": 16,
            "exchange_before": True,
            "exchange_max": True,
            "auto_fill": False,
            "shikigami_class": "N",
            "card_not_found_count": 0
        }
    },
    "i18n": {
        "KekkaiActivationSelf": "结界挂卡-self",
        "kekkai_activation_self_config": "结界挂卡-self配置",
        "star_priority": "星级优先级",
        "star_priority_help": "挂卡星级优先级排序，多个星级用>分隔，例如 5>6 表示优先选择5星卡，其次选择6星卡"
    }
}
