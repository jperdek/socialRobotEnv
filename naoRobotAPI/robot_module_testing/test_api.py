import json
from flask import Blueprint


def application_json_response(payload, status):
    return json.dumps(payload), status, {"content-type": "application/json"}


def text_response(payload, status = 200):
    return payload, status, {"content-type": "plain_text"}


ast_convertion_api = Blueprint("test_api", __name__, template_folder="templates")


@ast_convertion_api.route("/test", methods=["GET"])
def convert_python_code_to_ast():
    test = Test()
    return application_json_response()

