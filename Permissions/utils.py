import json
from . import permission as all_permissions
from accounts import models as User
from Permissions import utils as backend_utils
from rest_framework.renderers import JSONRenderer


def convert_serialized_data_to_json(data):
    json_string = JSONRenderer().render(data)
    json_string = json_string.decode('utf-8')
    json_string = json.loads(json_string)
    return json_string


def compare_and_update_permissions(data):
    try:
        all_permission = all_permissions.all_permissions
        for permission1 in data["permissions"]:
            for permission2 in all_permission:
                if permission1["module_name"] == permission2["module_name"]:
                    permission2.update(permission1)
                    break

        return all_permission
    except Exception as e:
        all_permission = all_permissions.all_permissions
        for permission1 in data:
            for permission2 in all_permission:
                if permission1["module_name"] == permission2["module_name"]:
                    permission2.update(permission1)
                    break
        return all_permission


def send_default_permissions():
    return all_permissions.all_permissions


def get_user_profile(username=None, code=None, email=None):
    try:
        if username and code:
            return User.objects.get(user__username=username, verification_code=code)
        if email and code:
            return User.objects.get(user__email=email, verification_code=code)
        if username:
            return User.objects.get(user__username=username)
        if email:
            return User.objects.get(user__email=email)
        if code:
            return User.objects.get(verification_code=code)

        backend_utils.logger("Username or email not provided!")
        return None
    except User.DoesNotExist as exep:
        backend_utils.logger(str(exep))
        return None

def failure_response(status_code=None, errors=None, msg='Operation Failure'):
    response = {
        'success': False,
        'message': msg,
        'errors': errors
    }
    if status_code:
        pass
        # response["status_code"] = status_code
    return response

def success_response(status_code=None, data=None, msg='Operation Success!'):
    response = {
        'success': True,
        'message': msg,
        'data': data
    }
    if status_code:
        pass
        # response["status_code"] = status_code
    return response
