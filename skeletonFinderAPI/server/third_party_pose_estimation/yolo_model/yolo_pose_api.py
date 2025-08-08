import json
from flask import Blueprint, request

from .pose_estimate import evaluate_yolo_pose_from_image, evaluate_yolo_pose_from_video


def application_json_response(payload, status):
    return json.dumps(payload), status, {"content-type": "application/json"}


def text_response(payload, status=200):
    return payload, status, {"content-type": "plain_text"}


yolo_pose_api = Blueprint("yolo_pose_api", __name__, template_folder="templates")


@yolo_pose_api.route("/pose_from_image", methods=["POST"])
def pose_from_image():
    encoded_image = request.get_data().decode("utf-8", "ignore")
    evaluation_response = list(evaluate_yolo_pose_from_image(source=encoded_image, is_base64encoded=True))
    return application_json_response(evaluation_response, 200)


@yolo_pose_api.route("/pose_from_video", methods=["POST"])
def pose_from_video():
    encoded_video = request.get_data().decode("utf-8", "ignore")
    number_frames_per_sec = int(request.args.get("number_frames_per_sec", 1))
    number_seconds_to_process = int(request.args.get("number_seconds_to_process", -1))
    evaluation_response = list(
        evaluate_yolo_pose_from_video(source=encoded_video, number_frames_per_sec=number_frames_per_sec,
                                      number_seconds_to_process=number_seconds_to_process,
                                      is_base64encoded=True))
    return application_json_response(evaluation_response, 200)
