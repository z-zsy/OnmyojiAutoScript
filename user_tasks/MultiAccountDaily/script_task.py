# This Python file uses the following encoding: utf-8
# @author runhey
# github https://github.com/runhey
from datetime import datetime, timedelta

from module.exception import TaskEnd, RequestHumanTakeover
from module.logger import logger
from tasks.Component.SwitchAccount.switch_account import SwitchAccount
from tasks.Component.SwitchAccount.switch_account_config import AccountInfo
from user_tasks.MultiAccountDaily.assets import MultiAccountDailyAssets
from user_tasks.MultiAccountDaily.config import MultiAccountDaily
from tasks.GameUi.game_ui import GameUi


class ScriptTask(GameUi, MultiAccountDailyAssets):
    mad_config: MultiAccountDaily = None

    def run(self):
        self.mad_config = self.config.multi_account_daily
        con = self.mad_config.multi_account_daily_config

        if not con.sub_account_list:
            logger.warning("小号列表为空，请在配置中填入小号账号信息！")
            self.set_next_run("MultiAccountDaily", target=datetime.now() + timedelta(hours=1))
            raise TaskEnd("MultiAccountDaily")

        for account_info in con.sub_account_list:
            logger.info("开始小号自动化流程 %s-%s", account_info.character, account_info.svr)

            if not self.is_need_run(account_info):
                logger.warning("%s 今日已完成日常 (上次完成时间: %s), 跳过", account_info.character, account_info.last_complete_time)
                continue

            # 1. 自动切号登录
            suc = SwitchAccount(self.config, self.device, account_info).switchAccount()
            if not suc:
                logger.warning("切换到小号 %s-%s 失败，尝试下一个小号", account_info.character, account_info.svr)
                continue

            # 2. 自动运行任务: 金币妖怪
            if con.enable_gold_youkai:
                try:
                    logger.hr("小号运行: 金币妖怪")
                    gold_youkai = self.CreatObjectFromModule("GoldYoukai", config=self.config, device=self.device)
                    gold_youkai.run()
                except TaskEnd:
                    logger.info("小号金币妖怪任务完成")
                except Exception as e:
                    logger.error(f"小号运行金币妖怪异常: {e}")

            # 3. 自动运行任务: 经验妖怪
            if con.enable_experience_youkai:
                try:
                    logger.hr("小号运行: 经验妖怪")
                    exp_youkai = self.CreatObjectFromModule("ExperienceYoukai", config=self.config, device=self.device)
                    exp_youkai.run()
                except TaskEnd:
                    logger.info("小号经验妖怪任务完成")
                except Exception as e:
                    logger.error(f"小号运行经验妖怪异常: {e}")

            # 4. 自动运行任务: 每日琐事 / 每日任务
            if con.enable_daily_trifles:
                try:
                    logger.hr("小号运行: 每日琐事")
                    daily_trifles = self.CreatObjectFromModule("DailyTrifles", config=self.config, device=self.device)
                    daily_trifles.run()
                except TaskEnd:
                    logger.info("小号每日琐事任务完成")
                except Exception as e:
                    logger.error(f"小号运行每日琐事异常: {e}")

            # 5. 更新完成记录并保存配置
            self.mad_config.update_account_login_history(account_info)
            self.save_config()
            logger.info("小号 %s-%s 今日日常全部完成！", account_info.character, account_info.svr)

        # 全套小号完成，设定次日 17:00 点再次执行
        next_time = datetime.now().replace(hour=17, minute=0, second=0, microsecond=0)
        if next_time <= datetime.now():
            next_time += timedelta(days=1)

        self.set_next_run("MultiAccountDaily", target=next_time)
        logger.info("全套小号自动化日常执行完毕，下一次运行时间: %s", next_time)
        raise TaskEnd("MultiAccountDaily")

    def is_need_run(self, item: AccountInfo) -> bool:
        last_time = item.last_complete_time
        if not last_time:
            return True

        now = datetime.now()
        today_17pm = now.replace(hour=17, minute=0, second=0, microsecond=0)

        if now >= today_17pm:
            return last_time < today_17pm
        else:
            yesterday_17pm = today_17pm - timedelta(days=1)
            return last_time < yesterday_17pm

    def CreatObjectFromModule(self, task_name: str, **kwargs):
        import importlib.util
        from pathlib import Path
        module_name = 'script_task'
        module_file = Path.cwd() / 'tasks' / task_name / (module_name + '.py')
        if not module_file.exists():
            user_file = Path.cwd() / 'user_tasks' / task_name / (module_name + '.py')
            if user_file.exists():
                module_file = user_file
        module_path = str(module_file)

        spec = importlib.util.spec_from_file_location(module_name, module_path)
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)

        TQEX = type("TQEX", (module.ScriptTask,), {})
        return TQEX(**kwargs)
