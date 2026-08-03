# This Python file uses the following encoding: utf-8
# @author runhey
# github https://github.com/runhey
from pydantic import BaseModel, Field
from tasks.Component.config_base import ConfigBase, Time
from tasks.Component.config_scheduler import Scheduler
from tasks.Dokan.config import (
    AttackDokanMasterType,
    AttackAccountConfig,
    DokanConfig as BaseDokanConfig,
    DokanBattleConfig,
)
from tasks.Component.SwitchSoul.switch_soul_config import SwitchSoulConfig


class DokanConfigSelf(BaseDokanConfig):
    only_attack_target_icon: bool = Field(default=True, description='只打带有【鑫】字寮徽标志的道馆')
    fallback_random_if_not_found: bool = Field(default=False, description='刷新上限用完仍未找到【鑫】字道馆时，是否保底挑战其他道馆（默认关闭）')


class DokanSelf(ConfigBase):
    scheduler: Scheduler = Field(default_factory=Scheduler)
    dokan_config: DokanConfigSelf = Field(default_factory=DokanConfigSelf)
    dokan_member_battle_conf: DokanBattleConfig = Field(default_factory=DokanBattleConfig)
    dokan_owner_battle_conf: DokanBattleConfig = Field(default_factory=DokanBattleConfig)
    dokan_member_switch_soul: SwitchSoulConfig = Field(default_factory=SwitchSoulConfig)
    dokan_owner_switch_soul: SwitchSoulConfig = Field(default_factory=SwitchSoulConfig)
    attack_count_config: AttackAccountConfig = Field(default_factory=AttackAccountConfig)


DokanConfig = DokanConfigSelf
