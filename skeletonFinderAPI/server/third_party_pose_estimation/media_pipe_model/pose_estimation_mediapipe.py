import base64
import io
from typing import Dict

# Taken from https://github.com/Ahmed-AI-01/Nao_Mimc/blob/main/Pose_est.py

import cv2
import mediapipe as mp
import numpy as np
from PIL import Image

mp_drawing = mp.solutions.drawing_utils
mp_pose = mp.solutions.pose


def evaluate_pose_mediapipe(orig_image: str, min_detection_confidence: float = 0.5,
                            min_tracking_confidence: float = 0.5, is_base64encoded: bool = True,
                            attach_visualization: bool = False) -> Dict:
    orig_image = base64.b64decode(orig_image) if is_base64encoded else orig_image

    pose_configuration = {}
    with Image.open(io.BytesIO(orig_image)) as img:
        image = cv2.cvtColor(np.array(img), cv2.COLOR_BGR2RGB)  # convert frame to RGB

        # Setup mediapipe_pose instance
        with mp_pose.Pose(min_detection_confidence=min_detection_confidence,
                          min_tracking_confidence=min_tracking_confidence) as pose:
            # Recolor image to RGB
            image = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)
            image.flags.writeable = False

            # Make detection
            results = pose.process(image)

            # Recolor back to BGR
            image.flags.writeable = True
            image = cv2.cvtColor(image, cv2.COLOR_RGB2BGR)
            # Define the names of the landmarks
            pose_names = ["Left shoulder", "Right shoulder", "Left elbow", "Right elbow", "Left wrist", "Right wrist"]

            # Extract landmarks
            try:
                pose_landmarks = results.pose_landmarks.landmark
                # Upper body points are from 11 to 16 and 23 to 28
                upper_body_landmarks = pose_landmarks[11:16]

                # Print and write each landmark's name and coordinates
                for i, landmark in enumerate(upper_body_landmarks):
                    pose_configuration[pose_names[i]] = {}
                    pose_configuration[pose_names[i]]["x"] = landmark.x
                    pose_configuration[pose_names[i]]["y"] = landmark.y
                    pose_configuration[pose_names[i]]["z"] = landmark.z
            except Exception as e:
                print("Cannot get human body landmarks using mediapipe: " + str(e))
                pose_configuration[pose_names[i]] = "Cannot get due to error."

            if attach_visualization:
                # Render detections
                mp_drawing.draw_landmarks(image, results.pose_landmarks, mp_pose.POSE_CONNECTIONS,
                                          mp_drawing.DrawingSpec(color=(245, 117, 66), thickness=2, circle_radius=2),
                                          mp_drawing.DrawingSpec(color=(245, 66, 230), thickness=2, circle_radius=2)
                                          )
                visualization_image = Image.fromarray(np.uint8(image)).convert('RGB')
                visualization_byte_array = io.BytesIO()
                visualization_image.save(visualization_byte_array, format='PNG')
                pose_configuration["visualization_base64"] = base64.b64encode(
                    visualization_byte_array.getvalue()).decode("utf-8")
    return pose_configuration
