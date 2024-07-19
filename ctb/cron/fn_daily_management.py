import pymysql
from os import getenv
from datetime import datetime, timezone, timedelta
from google.cloud import storage
from settings import CTB_LOGIN_URL, SUPPORT_EMAIL, CTB_REVIEWER_EMAIL, mysql_config_for_cloud_functions, send_ctb_email

# expirations and warning days
MAX_INACTIVE_PERIOD_DAYS = int(getenv("MAX_INACTIVE_PERIOD_DAYS", '60'))
WARNING_EXPIRATION_BEFORE_DAYS = int(getenv("WARNING_EXPIRATION_BEFORE_DAYS", '10'))
SECOND_WARNING_EXPIRATION_BEFORE_DAYS = int(getenv("SECOND_WARNING_EXPIRATION_BEFORE_DAYS", '2'))
PASSWORD_WARNING_EXPIRATION_BEFORE_DAYS = int(getenv("PASSWORD_WARNING_EXPIRATION_BEFORE_DAYS", '14'))
SECOND_PASSWORD_WARNING_EXPIRATION_BEFORE_DAYS = int(getenv("SECOND_PASSWORD_WARNING_EXPIRATION_BEFORE_DAYS", '2'))
APPLICATION_EXPIRATION_DAYS = int(getenv("APPLICATION_EXPIRATION_DAYS", '365'))
GCP_APP_DOC_BUCKET = getenv("GCP_APP_DOC_BUCKET", 'ctb-dev-app-doc-files')


def warn_expiration_date_utc(expiration_in_days):
    return (datetime.now(timezone.utc) + timedelta(days=expiration_in_days)).date()


def warning_last_login_date_utc(expiration_in_days):
    return (datetime.now(timezone.utc) - timedelta(
        days=(MAX_INACTIVE_PERIOD_DAYS - expiration_in_days))).date()


# today's password expiration dates: calculate what date needs to be warned currently for the password expiration
def warning_password_expiration_date_utc(days_before_expiration):
    return (datetime.now(timezone.utc) + timedelta(days=days_before_expiration)).date()


def application_expiration_date_utc_strftime():
    return (datetime.now(timezone.utc) - timedelta(days=APPLICATION_EXPIRATION_DAYS)).date().strftime('%Y-%m-%d')


def deactivate_account(user_id):
    if user_id:
        connection = pymysql.connect(**mysql_config_for_cloud_functions)
        with connection.cursor() as cursor:
            sql = "UPDATE auth_user SET is_active=False WHERE id = %s"
            cursor.execute(sql, (user_id,))
        connection.commit()


def delete_blob(bucket_name, blob_name):
    """Deletes a blob from the bucket."""
    storage_client = storage.Client()
    bucket = storage_client.bucket(bucket_name)
    blob = bucket.blob(blob_name)
    if blob.exists(storage_client):
        generation_match_precondition = None
        # Optional: set a generation-match precondition to avoid potential race conditions
        # and data corruptions. The request to delete is aborted if the object's
        # generation number does not match your precondition.
        blob.reload()  # Fetch blob metadata to use in generation_match_precondition.
        generation_match_precondition = blob.generation
        blob.delete(if_generation_match=generation_match_precondition)
        print(f"[STATUS] {bucket_name}/{blob_name} deleted.")
    else:
        print(f"[STATUS] {bucket_name}/{blob_name} not found.")


DEACTIVE_ACCOUNT_WARNING = 1
SECOND_DEACTIVE_ACCOUNT_WARNING = 2
DEACTIVE_ACCOUNT_NOTIFICATION = 3
PASSWORD_EXPIRATION_WARNING = 4
SECOND_PASSWORD_EXPIRATION_WARNING = 5
PASSWORD_EXPIRATION_NOTIFICATION = 6


def send_notification_email(user_email, email_type):
    if email_type == DEACTIVE_ACCOUNT_WARNING or email_type == SECOND_DEACTIVE_ACCOUNT_WARNING:
        if email_type == DEACTIVE_ACCOUNT_WARNING:
            expiration_date = warn_expiration_date_utc(WARNING_EXPIRATION_BEFORE_DAYS)
            warning_period = WARNING_EXPIRATION_BEFORE_DAYS
        else:
            expiration_date = warn_expiration_date_utc(SECOND_WARNING_EXPIRATION_BEFORE_DAYS)
            warning_period = SECOND_WARNING_EXPIRATION_BEFORE_DAYS
        subject = f"[Chernobyl Tissue Bank] Your account will become deactivated in {warning_period} days"
        mail_content = '''
            Dear {user_email},<br><br>
            Your CTB account shows that you had no activity for a long time, and will expire on {expiration_date} ({warning_period} days from today).<br>
            Please visit <a href=\'{website}\' target=\'_blank\'>our website</a> and login to your account before it expires, to ensure uninterrupted access.<br>
            Any account that has not been logged in for {max_inactive_period} days or longer will become deactivated, but any stored
            information with the account will not be lost.<br>
            Once the account is deactivated, you will need to contact us to re-atviate your account.<br>
            If you need assistance with your login then please email us at {support_email}.<br><br>
            Sincerely,<br>
            Chernobyl Tissue Bank Team'''.format(
            user_email=user_email, expiration_date=expiration_date,
            warning_period=warning_period,
            max_inactive_period=MAX_INACTIVE_PERIOD_DAYS,
            website=CTB_LOGIN_URL, support_email=SUPPORT_EMAIL)
        print(
            f"[STATUS] Sending a notification to {user_email} of the account deactivation in {warning_period} days.")
    elif email_type == DEACTIVE_ACCOUNT_NOTIFICATION:
        subject = "[Chernobyl Tissue Bank] Your account has been deactivated"
        mail_content = '''
            Dear {user_email},<br><br>
            Your CTB account has been deactivated due to {max_inactive_period} days of inactivity.<br>
            Please contact {support_email} in order to reactivate your account.<br>
            If you would like more information regarding CTB policies on account deactivation, please contact {support_email}.<br><br>
            Sincerely,
            Chernobyl Tissue Bank Team'''.format(
            user_email=user_email, max_inactive_period=MAX_INACTIVE_PERIOD_DAYS,
            support_email=SUPPORT_EMAIL)
        print(f"[STATUS] Sending a notification to {user_email} of the account deactivation.")
    elif email_type == PASSWORD_EXPIRATION_WARNING or email_type == SECOND_PASSWORD_EXPIRATION_WARNING:
        if email_type == PASSWORD_EXPIRATION_WARNING:
            expiration_date = warning_password_expiration_date_utc(PASSWORD_WARNING_EXPIRATION_BEFORE_DAYS)
            warning_period = PASSWORD_WARNING_EXPIRATION_BEFORE_DAYS
        else:
            expiration_date = warning_password_expiration_date_utc(SECOND_WARNING_EXPIRATION_BEFORE_DAYS)
            warning_period = SECOND_PASSWORD_WARNING_EXPIRATION_BEFORE_DAYS
        subject = f"[Chernobyl Tissue Bank] Your password is expiring in {warning_period} days"

        mail_content = '''
            Dear {user_email},<br><br>
            Your CTB account password will expire on {expiration_date} ({warning_period} days from today).<br>
            Please visit <a href=\'{website}\' target=\'_blank\'>our website</a> to change your password before it expires, to ensure uninterrupted access.<br>
            To access this webpage you must know your username and current password.<br>
            Your new password will expire in 120 days after you change it.<br>
            If you need assistance with your login then please email us at {support_email}.<br><br>
            Sincerely,<br>
            Chernobyl Tissue Bank Team'''.format(
            user_email=user_email, expiration_date=expiration_date,
            warning_period=warning_period,
            website=CTB_LOGIN_URL, support_email=SUPPORT_EMAIL)
        print(
            f"[STATUS] Sending a notification to {user_email} of the password expiration in {warning_period} days.")
    else:  # PASSWORD_EXPIRATION_NOTIFICATION
        subject = "[Chernobyl Tissue Bank] Your account password has expired."
        mail_content = '''
            Dear {user_email},<br><br>
            Your CTB account password has been expired.<br>
            Please visit <a href=\'{website}\' target=\'_blank\'>our website</a> to change your password in order to access the Biosample Search Facility.<br>
            To access this webpage you must know your username and current password.<br>
            If you need assistance, please email us at {support_email}.<br><br>
            Sincerely,<br>
            Chernobyl Tissue Bank Team'''.format(
            user_email=user_email,
            website=CTB_LOGIN_URL,
            support_email=SUPPORT_EMAIL)
        print(f"[STATUS] Sending a notification to {user_email} of the password expiration.")
    send_ctb_email(to_list=[user_email], subject=subject, mail_content=mail_content, bcc_ctb_reviewer=False)


def sync_password_expiration_date_time(user_id):
    connection = pymysql.connect(**mysql_config_for_cloud_functions)
    with connection.cursor() as cursor:
        update_statement = f'''
                            UPDATE accounts_passwordexpiration
                            SET expiration_date = NOW()
                            WHERE user_id = {user_id} AND expiration_date > NOW()'''
        cursor.execute(update_statement)
        connection.commit()


def manage_accounts(request):
    print('== calling manage_accounts() ==')
    connection = pymysql.connect(**mysql_config_for_cloud_functions)
    warn_password_expiration_user_list = []
    second_warn_password_expiration_user_list = []
    password_expiration_user_list = []
    warn_inactivation_user_list = []
    second_warn_inactivation_user_list = []
    inactivate_user_list = []

    with connection.cursor() as cursor:
        # retrieve user info
        select_user_sql = '''
        SELECT u.id, u.last_login, u.username, u.email, u.date_joined, p.expiration_date
        FROM auth_user u
        LEFT JOIN accounts_passwordexpiration p
        ON u.id = p.user_id
        WHERE u.is_active=True AND u.is_staff=False'''
        cursor.execute(select_user_sql)
        user_list = cursor.fetchall()

        approval_pending_user_list = []
        if datetime.today().weekday() < 4 or datetime.today().weekday() == 6:     # Sun - Thur
            select_user_group_sql = '''
                SELECT u.email
                FROM auth_user u
                LEFT JOIN auth_user_groups g
                ON u.id = g.user_id
                LEFT JOIN account_emailaddress e
                ON e.user_id = u.id
                WHERE u.is_active = True
                AND u.is_staff = False
                AND g.group_id IS NULL
                AND e.verified = True;'''
            cursor.execute(select_user_group_sql)
            approval_pending_user_list = cursor.fetchall()

    for user_item in user_list:
        user_last_access = user_item.get("last_login") or user_item.get("date_joined")
        if user_last_access:
            user_last_access_date = user_last_access.date()
            if user_last_access_date == warning_last_login_date_utc(WARNING_EXPIRATION_BEFORE_DAYS):
                warn_inactivation_user_list.append(user_item)
            elif user_last_access_date == warning_last_login_date_utc(SECOND_WARNING_EXPIRATION_BEFORE_DAYS):
                second_warn_inactivation_user_list.append(user_item)
            elif user_last_access_date == warning_last_login_date_utc(0):
                inactivate_user_list.append(user_item)
        password_expiration = user_item.get("expiration_date")
        if password_expiration:
            password_expiration_date = password_expiration.date()
            if password_expiration_date == warning_password_expiration_date_utc(
                    PASSWORD_WARNING_EXPIRATION_BEFORE_DAYS):
                warn_password_expiration_user_list.append(user_item)
            elif password_expiration_date == warning_password_expiration_date_utc(
                    SECOND_WARNING_EXPIRATION_BEFORE_DAYS):
                second_warn_password_expiration_user_list.append(user_item)
            elif password_expiration_date == warning_password_expiration_date_utc(0):
                password_expiration_user_list.append(user_item)

    for ia_warn_user in warn_inactivation_user_list:
        user_email = ia_warn_user.get("email", "")
        send_notification_email(user_email, DEACTIVE_ACCOUNT_WARNING)
    for ia_warn_user in second_warn_inactivation_user_list:
        user_email = ia_warn_user.get("email", "")
        send_notification_email(user_email, SECOND_DEACTIVE_ACCOUNT_WARNING)
    for inactive_user in inactivate_user_list:
        deactivate_account(inactive_user.get("id"))
        user_email = inactive_user.get("email", "")
        send_notification_email(user_email, DEACTIVE_ACCOUNT_NOTIFICATION)

    for pe_warn_user in warn_password_expiration_user_list:
        user_email = pe_warn_user.get("email", "")
        send_notification_email(user_email, PASSWORD_EXPIRATION_WARNING)

    for pe_warn_user in second_warn_password_expiration_user_list:
        user_email = pe_warn_user.get("email", "")
        send_notification_email(user_email, SECOND_PASSWORD_EXPIRATION_WARNING)

    for pe_user in password_expiration_user_list:
        user_email = pe_user.get("email", "")
        send_notification_email(user_email, PASSWORD_EXPIRATION_NOTIFICATION)
        # expire user's password manually to sync with the email notification
        sync_password_expiration_date_time(pe_user.get("id"))

    pending_account_list = []
    for pending_user in approval_pending_user_list:
        pending_account_list.append(pending_user.get("email", ""))

    pending_account_count = len(pending_account_list)
    if pending_account_count:
        is_or_are = "are" if pending_account_count > 1 else "is"
        is_plural = "s" if pending_account_count > 1 else ""
        it_or_them = "them" if pending_account_count > 1 else "it"
        html_pending_user_list = "<ul><li>" + "</li><li>".join(pending_account_list) + "</li></ul>"
        subject = f"[Chernobyl Tissue Bank] Approval pending account{is_plural}"
        mail_content = f'''
        This is an email to inform you that there {is_or_are} {pending_account_count} new CTB account{is_plural}
        which {is_or_are} in pending status:<br/><br/>
        User account email:<br/>
        {html_pending_user_list}
        <br/><br/>
        Please evaluate the account{is_plural} above and inform the ISB-CGC team whether to approve or disapprove {it_or_them}.<br/>
        A user will not be able to access the biorepository until the account is approved.<br/>
        A disapproved account will be deactivated, and cannot be reused again without an admin's assistance.<br/><br/>
        ISB-CGC Team
        '''
        send_ctb_email(to_list=[CTB_REVIEWER_EMAIL], subject=subject, mail_content=mail_content,
                       bcc_ctb_reviewer=False)


def manage_applications(request):
    print('== calling manage_applications() ==')
    connection = pymysql.connect(**mysql_config_for_cloud_functions)
    submission_id_list = []
    with connection.cursor() as cursor:
        select_query = '''
                SELECT s.id, s.entry_form_path, s.summary_file_path
                FROM auth_user AS u
                LEFT JOIN donors_submissions AS s
                ON u.id = s.owner_id
                WHERE u.is_active=True 
                AND u.is_staff=False 
                AND s.active=True 
                AND s.submitted_date <= \'{application_expiration_date_utc_strftime}\''''.format(
            application_expiration_date_utc_strftime=application_expiration_date_utc_strftime())

        cursor.execute(select_query)
        submission_list = cursor.fetchall()
        for submission_item in submission_list:
            submission_id_list.append(str(submission_item.get("id")))
            entry_form_path = submission_item.get("entry_form_path")
            bucket_name = GCP_APP_DOC_BUCKET
            if entry_form_path:
                print(f"[STATUS] Deleting an expired application from bucket: {bucket_name}/{entry_form_path}")
                delete_blob(bucket_name, entry_form_path)

            summary_file_path = submission_item.get("summary_file_path")
            if summary_file_path:
                print(
                    f"[STATUS] Deleting an expired application summary from bucket: {bucket_name}/{summary_file_path}")
                delete_blob(bucket_name, summary_file_path)

        # deactivate records in DB
        if len(submission_id_list):
            submission_id_list_str = ",".join(submission_id_list)
            update_statement = '''
                    UPDATE donors_submissions
                    SET active = 0
                    WHERE id IN ({submission_id_list_str})'''.format(
                submission_id_list_str=submission_id_list_str)
            cursor.execute(update_statement)
            connection.commit()
            print(
                f"[STATUS] Inactivating expired application(s) from the DB: donors_submissions_id:[{submission_id_list}]")


def daily_management(request):
    try:
        manage_accounts(None)
        manage_applications(None)
        return {"code": 200, "message": "Function [daily_management] has been run successfully."}
    except Exception as e:
        print(f'[Error] {e}')
        return {"code": 500, "message": f"Function [daily_management] failed to run: {e}"}
