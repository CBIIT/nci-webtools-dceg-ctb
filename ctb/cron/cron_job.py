from django_cron import CronJobBase, Schedule
from fn_daily_management import daily_management
from fn_account_approval import account_approval


class DailyManagementCronJob(CronJobBase):
    RUN_EVERY_MINS = 1440  # 1440 minutes = 24 hours

    schedule = Schedule(run_every_mins=RUN_EVERY_MINS)
    code = 'ctb.daily_management'  # a unique code for cron job
    code2 = 'ctb.account_approval'  # a unique code for cron job

    def do(self):
        # Assuming daily_management is a standalone function you can call
        # If it's part of a class, you'll need to instantiate that class first
        try:
            account_approval()
            daily_management()
            print("[STATUS] Functions [fn_daily_management] and [fn_account_approval] have been run successfully")
        except Exception as e:
            print(f'[Error] {e}')

