# This Python file uses the following encoding: utf-8
# @author runhey
# github https://github.com/runhey
from datetime import datetime
from pydantic import BaseModel, Field
from tasks.Component.config_base import ConfigBase, TimeDelta
from tasks.Component.config_scheduler import Scheduler
from tasks.Component.SwitchAccount.switch_account_config import AccountInfo


class MultiAccountDailyScheduler(Scheduler):
    priority: int = Field(default=2, description='priority_help')
    success_interval: TimeDelta = Field(default=TimeDelta(days=1), description='success_interval_help')
    failure_interval: TimeDelta = Field(default=TimeDelta(hours=1), description='failure_interval_help')
    server_update: str = Field(default="17:00:00", description='每日触发时间，设为17点后自动运行')


class MultiAccountDailyConfig(BaseModel):
    enable_gold_youkai: bool = Field(default=True, description='是否自动完成金币妖怪')
    enable_experience_youkai: bool = Field(default=True, description='是否自动完成经验妖怪')
    enable_daily_trifles: bool = Field(default=True, description='是否自动完成每日琐事/日常任务')

    sub_account_list: list[AccountInfo] = Field(
        default_factory=list,
        description='小号列表配置。包含账号、掩码别名、服务器名、角色名等信息'
    )


class MultiAccountDaily(ConfigBase):
    scheduler: MultiAccountDailyScheduler = Field(default_factory=MultiAccountDailyScheduler)
    multi_account_daily_config: MultiAccountDailyConfig = Field(default_factory=MultiAccountDailyConfig)

    def update_account_login_history(self, item: AccountInfo):
        for account in self.multi_account_daily_config.sub_account_list:
            if account.account == item.account and account.character == item.character and account.svr == item.svr:
                account.last_complete_time = datetime.now()
                break
