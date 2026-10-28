from .fn_daily_management import daily_management

import logging
import threading
import time

logger = logging.getLogger('main_logger')


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

class DailyManagementCronJob:
    def do(self):
        try:
            logger.info("Running daily management")
            daily_management(None)
            logger.info("Daily management completed")
        except Exception:
            logger.exception("Daily management failed")
