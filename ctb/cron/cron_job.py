from django_cron import CronJobBase, Schedule
from fn_daily_management import daily_management
from fn_account_approval import account_approval

import threading
import time
 
def daily_task():
    DailyManagementCronJob().do()
 
def schedule_task(interval, task):
    def wrapper():
        while True:
            time.sleep(interval)
            task()
   
    scheduler_thread = threading.Thread(target=wrapper)
    scheduler_thread.daemon = True
    scheduler_thread.start()
 
# execute every day
#schedule_task(60 * 60 * 24, daily_task) 



class DailyManagementCronJob(CronJobBase):
    #RUN_EVERY_MINS = 1440  # 1440 minutes = 24 hours

    #schedule = Schedule(run_every_mins=RUN_EVERY_MINS)
    #code = 'ctb.daily_management'  # a unique code for cron job
    #code2 = 'ctb.account_approval'  # a unique code for cron job

    def do(self):
        try:
            print("trying to run daily management")
            account_approval()
            daily_management()
            print("[STATUS] Functions [fn_daily_management] and [fn_account_approval] have been run successfully")
        except Exception as e:
            print(f'[Error] {e}')

