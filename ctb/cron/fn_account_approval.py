import pymysql
from os import getenv
from ..settings import mysql_config_for_cloud_functions, send_ctb_email, SUPPORT_EMAIL, CTB_LOGIN_URL

GROUP_NAME = getenv("GROUP_NAME", "ctb_team")
GCLOUD_PROJECT_ID= getenv("GCLOUD_PROJECT_ID", "dev")
TIER = GCLOUD_PROJECT_ID.replace('nih-nci-cbiit-ctb-', '')



def set_account_approval_stat(user_email=None, is_approved=None):
    print("trying to run set_account_approval_stat", user_email, is_approved)
    if user_email is None:
        return {"code": 500,
                "message": f"Function [set_account_approval_stat] failed to run: account email is not provided"}
    if is_approved is None:
        return {"code": 500,
                "message": f"Function [set_account_approval_stat] failed to run: approved status is not provided"}
    try:
        connection = pymysql.connect(**mysql_config_for_cloud_functions)
        print("connection: ", connection)
        with connection.cursor() as cursor:
            select_user_id_query = f'''
                SELECT id FROM auth_user
                WHERE email = \'{user_email}\' and is_staff = 0;
            '''
            select_group_id_query = f'''
                SELECT id FROM auth_group
                WHERE name =  '{GROUP_NAME}';
            '''
            cursor.execute(select_user_id_query)
            
            user_list = cursor.fetchall()
            print("user_list: ", user_list)
            if len(user_list) == 1:
                # success
                user_id = user_list[0].get('id')
                cursor.execute(select_group_id_query)
                group_list = cursor.fetchall()
                is_active = 1 if is_approved else 0
                # update user's active status
                update_user_stat_query = f'''
                    UPDATE auth_user
                    SET is_active = {is_active}
                    WHERE id =  {user_id};
                '''
                cursor.execute(update_user_stat_query)
                connection.commit()
                if len(group_list) == 1:
                    group_id = group_list[0].get('id')
                    select_user_group_query = f'''
                        SELECT id FROM auth_user_groups
                        WHERE user_id =  {user_id} AND group_id = {group_id};
                    '''
                    cursor.execute(select_user_group_query)
                    user_group_list = cursor.fetchall()

                    if len(user_group_list) == 0:
                        if is_approved:
                            insert_user_group_statement = f'''
                                INSERT INTO auth_user_groups (user_id, group_id)
                                VALUES ({user_id}, {group_id} );
                            '''
                            cursor.execute(insert_user_group_statement)
                            connection.commit()
                    else:
                        if is_approved:
                            return {"code": 200,
                                    "message": f"Function [set_account_approval_stat] user {user_email} is already in group '{GROUP_NAME}'."}
                        else:
                            delete_user_group_statement = f'''
                                DELETE FROM auth_user_groups
                                WHERE user_id = {user_id} and group_id = {group_id};
                            '''
                            cursor.execute(delete_user_group_statement)
                            connection.commit()
                else:
                    return {"code": 500,
                            "message": f"Function [set_account_approval_stat] user group '{GROUP_NAME}' was not found."}

                if is_approved:
                    print("sending email")
                    mail_subject = f'{TIER}[Chernobyl Tissue Bank] Your account is approved'
                    mail_content = f'''
                        Dear {user_email},<br><br>
                        Your CTB account has been approved.<br>
                        Please visit <a href=\'{CTB_LOGIN_URL}\' target=\'_blank\'>our website</a> and log-in to access the Biosample Search Facility.<br><br>
                        If you need assistance, please email us at {SUPPORT_EMAIL}.<br><br><br>
                        Sincerely,<br><br>
                        Chernobyl Tissue Bank Team'''
                else:
                    mail_subject = f'{TIER}[Chernobyl Tissue Bank] Your account was disapproved'
                    mail_content = f'''
                        Dear {user_email},<br><br>
                        We are sorry to inform you that we were not able to approve your account.<br>
                        Please email us at {SUPPORT_EMAIL} if you have any questions.<br><br>
                        Sincerely,<br><br>
                        Chernobyl Tissue Bank Team'''
                send_ctb_email(to_list=[user_email], subject=mail_subject, mail_content=mail_content,
                               bcc_ctb_reviewer=True)
                return {"code": 200,
                        "message": "Function [account_approval] user account {user_email} is {status}".format(
                            user_email=user_email, status=('approved' if is_approved else 'disapproved'))}
            else:
                return {"code": 500,
                        "message": f"Function [set_account_approval_stat]: user {user_email} was not found."}
    except Exception as e:
        print(f'[Error] {e}')
        return {"code": 500, "message": f"Function [set_account_approval_stat] failed to run: {e}"}


def account_approval(request):
    print("trying to run account approval", request)
       
    try:
        connection = pymysql.connect(**mysql_config_for_cloud_functions)
        admin_token = request['admin_token']
        user_email = request['user_email']
        is_approved = request['is_approved']
        print("cursor: ", admin_token)
        with connection.cursor() as cursor:
            select_query = f'''
                    SELECT token
                    FROM django_token AS t 
                    where t.token = '{admin_token}' ;'''
            cursor.execute(select_query)
            print("cursor: ", cursor.rowcount)
            if cursor.rowcount == 0:
                return {"code": 500, "message": f"Function [account_approval] failed to run: admin token not found"}
            else:
                return set_account_approval_stat(user_email=user_email, is_approved=is_approved)
    except Exception as e:
        return {"code": 500, "message": f"Function [account_approval] failed to run: {e}"}
