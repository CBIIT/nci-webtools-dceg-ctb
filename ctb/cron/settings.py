import pymysql
from os import getenv
import requests

# mysql connection params
CONNECTION_NAME = getenv("CONNECTION_NAME")
DB_USER = getenv("DB_USER")
DB_PASSWORD = getenv("DB_PASSWORD")
DB_NAME = getenv("DB_NAME")



# mailgun api
EMAIL_SERVICE_API_KEY = getenv("EMAIL_SERVICE_API_KEY")
EMAIL_SERVICE_API_URL = getenv("EMAIL_SERVICE_API_URL")
NOTIFICATION_EMAIL_FROM_ADDRESS = getenv("NOTIFICATION_EMAIL_FROM_ADDRESS")

# website login url
CTB_LOGIN_URL = getenv("CTB_LOGIN_URL")
SUPPORT_EMAIL = getenv("SUPPORT_EMAIL", "ctb-support@isb-cgc.org")
CTB_REVIEWER_EMAIL = getenv("CTB_REVIEWER_EMAIL", "elee@isb-cgc.org")

INSTALLED_APPS = [
    # other Django apps...
    'django_cron',
]


mysql_config_for_cloud_functions = {
    'unix_socket': f'/cloudsql/{CONNECTION_NAME}',
    'user': DB_USER,
    'password': DB_PASSWORD,
    'db': DB_NAME,
    'charset': 'utf8mb4',
    'cursorclass': pymysql.cursors.DictCursor
}


def send_ctb_email(to_list, subject, mail_content, bcc_ctb_reviewer=False):
    bcc_list = ([CTB_REVIEWER_EMAIL] if bcc_ctb_reviewer else [])
    return requests.post(
        EMAIL_SERVICE_API_URL,
        auth=("api", EMAIL_SERVICE_API_KEY),
        data={"from": f"Chernobyl Tissue Bank no-reply <{NOTIFICATION_EMAIL_FROM_ADDRESS}>",
              "to": to_list,
              "bcc": bcc_list,
              "subject": subject,
              "html": mail_content})














