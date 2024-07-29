# import pymysql
from fn_daily_management import daily_management
from fn_account_approval import account_approval

CTB_CL_FN_DAILY_MANAGEMENT = 0
CTB_CL_FN_ACCOUNT_APPROVAL = 1


def ctb_functions(request):
    try:
        request_json = request.get_json(silent=True)
        request_args = request.args
        #
        # arguments: (ctb_cl_fn_type, user_email, is_approved)
        # * ctb_cl_fn_type:
        #   CTB_CL_FN_DAILY_MANAGEMENT(=0) - to run daily_management function (default)
        #   CTB_CL_FN_ACCOUNT_APPROVAL(=1) - to run account_approval function
        # * user_email: user email account
        # * is_approved: 1 for approved account, 0 for disapproved
        #
        ctb_cl_fn_type = 0
        if request_json and 'ctb_cl_fn_type' in request_json:
            ctb_cl_fn_type = request_json['ctb_cl_fn_type']
        elif request_args and 'ctb_cl_fn_type' in request_args:
            ctb_cl_fn_type = request_args['ctb_cl_fn_type']

        if ctb_cl_fn_type == CTB_CL_FN_DAILY_MANAGEMENT:
            return daily_management(request)
        else:
            return account_approval(request)

    except Exception as e:
        return {"code": 500, "message": f"Function [ctb_functions] failed to run: {e}"}


if __name__ == "__main__":
    ctb_functions(None)
