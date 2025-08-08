import json
from flask import Blueprint, request

from .pose_estimation_mediapipe import evaluate_pose_mediapipe


def application_json_response(payload, status):
    return json.dumps(payload), status, {"content-type": "application/json"}


def text_response(payload, status = 200):
    return payload, status, {"content-type": "plain_text"}


media_pipe_pose_api = Blueprint("media_pipe_pose_api", __name__, template_folder="templates")


@media_pipe_pose_api.route("/pose_from_image", methods=["POST"])
def pose_from_image():
    encoded_image = request.get_data().decode("utf-8", "ignore")
    attach_visualization = bool(request.args.get("attach_visualization", "False"))
    evaluation_response = evaluate_pose_mediapipe(encoded_image, attach_visualization = attach_visualization)
    return application_json_response(evaluation_response, 200)


@media_pipe_pose_api.route("/pose_from_video", methods=["POST"])
def pose_from_video():
    encoded_video = request.get_data().decode("utf-8", "ignore")
    attach_visualization = bool(request.args.get("attach_visualization", "False"))
    evaluation_response = evaluate_pose_mediapipe(encoded_video, attach_visualization = attach_visualization)
    return application_json_response(evaluation_response, 200)
