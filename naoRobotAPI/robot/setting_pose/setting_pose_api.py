import json
from flask import Blueprint, request

from setting_pose import set_nao_pose


def application_json_response(payload, status):
    return json.dumps(payload), status, {"content-type": "application/json"}


def text_response(payload, status=200):
    return payload, status, {"content-type": "plain_text"}


setting_pose_api = Blueprint("setting_pose_api", __name__, template_folder="templates")


@setting_pose_api.route("/setPose", methods=["POST"])
def set_pose():
    angles_dict = request.get_data().decode("utf-8", "ignore")
    set_nao_pose(angles_dict)
    return application_json_response({"success": True}, 200)
