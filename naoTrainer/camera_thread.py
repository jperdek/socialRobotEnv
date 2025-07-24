from datetime import datetime
from PySide6.QtCore import *
from PySide6.QtGui import *
from PySide6.QtWidgets import *
import cv2

# from fer.emonetModel import EmonetModel
from realsense_depth import *
from fer.fer_controller import FerController

from fer.deepFaceModel import DeepFaceModel
from fer.affectNetCnn import AffectNetModel
# from fer.cageModel import CageModel

import mediapipe as mp

import time
import math

from exercise_poses.helper_poses.poses_arms import ArmsPose
from exercise_poses.helper_poses.poses_legs import LegsPose
from exercise_poses.helper_poses.poses_sit import SitPose

import traceback


class CameraThread(QThread):

    def __init__(self, app_instance_arg=None):
        super(CameraThread, self).__init__()  # Calling the parent class's __init__ method
        # Set up the Mediapipe pose estimation
        self.mp_pose = mp.solutions.pose.Pose(
            min_detection_confidence=0.5,
            min_tracking_confidence=0.5)
        self.app_instance = app_instance_arg
        self.camera = DepthCamera()
        self.stoji = "unset"

        self.arms_poses = ArmsPose()
        self.legs_poses = LegsPose()
        self.sit_poses = SitPose()

    last_frame_time = time.time()

    # Define a signal to emit the camera frame when it is captured
    frame_captured = Signal(QImage, str)
    exercise_label_signal = Signal(str)
    score_signal = Signal(bool)
    stage_signal = Signal(str, str, int)
    update_distance_signal = Signal(int)

    # Get Warnings from robot
    exercise_interrupt_signal = Signal()
    received_robot_signal = Signal(str)

    can_do_detection = False
    current_exercise = None
    fer = FerController()
    can_detect_em = False
    check_response_end = False
    debug_up = True
    camera_mode = 'depth'

    usb_brio_input = 2  # cable input number for cv2 from usb-c

    face_net = cv2.dnn.readNetFromCaffe(
        "deploy.prototxt",  # Path to prototxt
        "res10_300x300_ssd_iter_140000.caffemodel"  # Pretrained weights
    )

    def run(self):
        mp_drawing = mp.solutions.drawing_utils

        if self.can_detect_em:
            cap = cv2.VideoCapture(self.usb_brio_input)
            cap.set(cv2.CAP_PROP_FRAME_WIDTH, 3840)
            cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 2160)

        while True:
            print("Running....")
            try:
                # Read a frame from the camera
                ret, depth, frame = self.camera.get_frame()
                if self.can_detect_em:
                    ret_webcam, brio_frame = cap.read()

                # Check if the frame was successfully retrieved
                if not ret:
                    print("Error: Unable to read from camera")
                    continue

                height, width, channels = frame.shape
                bytes_per_line = channels * width

                if self.can_detect_em:
                    h, w = brio_frame.shape[:2]
                    blob = cv2.dnn.blobFromImage(brio_frame, 1.0, (300, 300),
                                                 (104.0, 177.0, 123.0), False, False)
                    self.face_net.setInput(blob)
                    detections = self.face_net.forward()

                    for i in range(detections.shape[2]):
                        confidence = detections[0, 0, i, 2]
                        if confidence > 0.45:
                            box = detections[0, 0, i, 3:7] * [w, h, w, h]
                            x1, y1, x2, y2 = box.astype("int")

                            pad = 20
                            x1 = max(0, x1 - pad)
                            y1 = max(0, y1 - pad)
                            x2 = min(w, x2 + pad)
                            y2 = min(h, y2 + pad)

                            brio_frame = brio_frame[y1:y2, x1:x2]
                            brio_frame = cv2.resize(brio_frame, None, fx=1.25, fy=1.25,
                                                    interpolation=cv2.INTER_CUBIC)  # alebo  INTER_LANCZOS4

                    brio_frame = self.fer.detectEmotion(brio_frame)

                    if self.check_response_end:
                        self.exercise_interrupt_signal.emit()

                # Perform MediaPipe pose estimation
                results = self.mp_pose.process(frame)

                # if width == 1920:
                #     frame_np = np.array(frame.data, dtype=np.uint8)  # Convert to NumPy array
                #     frame = cv2.resize(frame_np, (1280, 720))  # Resize

                # Draw landmarks if available
                if results and results.pose_landmarks is not None:

                    mp_drawing.draw_landmarks(
                        frame, results.pose_landmarks, mp.solutions.pose.POSE_CONNECTIONS,
                        mp_drawing.DrawingSpec(
                            color=(245, 117, 66), thickness=2, circle_radius=2),
                        mp_drawing.DrawingSpec(
                            color=(245, 66, 230), thickness=2, circle_radius=2))

                    landmarks = self.get_pose_estimation_landmarks(frame)

                    nose_distance, nose_coordinates = self.get_nose_distance_coordinates(
                        frame, depth)

                    if self.debug_up and self.current_exercise != None:
                        self.current_exercise.visual_debug_up(frame, landmarks)

                    # Emit the nose distance
                    self.update_distance_signal.emit(nose_distance)

                if self.camera_mode == 'depth':
                    if width == 1920:
                        height, width, channels = frame.shape
                        bytes_per_line = width * channels

                    # Convert to QImage and emit the signal
                    qimage = QImage(frame.data, width, height, bytes_per_line, QImage.Format_BGR888)
                    self.frame_captured.emit(qimage, self.fer.domimant_em_text)

                else:
                    brio_frame = cv2.resize(brio_frame, (1280, 720))  # Resize
                    height, width, channel = brio_frame.shape
                    bytes_per_line = 3 * width

                    # Convert to QImage and emit the signal
                    qimage = QImage(brio_frame.data, width, height, bytes_per_line, QImage.Format_BGR888)
                    self.frame_captured.emit(qimage, self.fer.domimant_em_text)
            except Exception as e:
                # Log the error for debugging purposes
                print(f"Error during processing: {e}")
                # Optionally re-initialize the pose processor to reset state
                self.mp_pose = mp.solutions.pose.Pose()

    def initialize_fer(self, can_detect_em, fer_model: Optional[str]):  # Set up face emotion recognition
        print("initializing FER", can_detect_em, fer_model)

        self.can_detect_em = can_detect_em

        if self.can_detect_em and fer_model:
            if fer_model == "deepFace":
                fer_model = DeepFaceModel()
            elif fer_model == "affectnet":
                fer_model = AffectNetModel()
            # elif fer_model == "emonet":
            #     fer_model = EmonetModel()
            # elif fer_model == "cagenet":
            #     fer_model = CageModel()

            self.fer.fer_model = fer_model

    def change_camera(self, camera_mode):
        print("Camera_mode", camera_mode)
        self.camera_mode = camera_mode

    def on_exercise_state_changed(self, message):

        if "ExerciseContinue" in message:
            self.current_exercise.exercise_lock = False

            if self.current_exercise.base_pose_time_treshold != 0:
                self.current_exercise.base_pose_time_treshold = None

            if self.current_exercise.wrong_pose_time_treshold != 0:
                self.current_exercise.wrong_pose_time_treshold = None

        if "getEmotion_start" in message:
            self.stage_signal.emit("fer_start", self.fer.aggregateEmotions(), 0)

        elif "getEmotion_end" in message:
            print("sending to emit")
            self.stage_signal.emit("fer_end", self.fer.aggregateEmotions(), 0)

        elif "getEmotion_forefootingStart" in message:
            self.stage_signal.emit("fer_forefooting_start", self.fer.aggregateEmotions(), 0)

        elif "getEmotion_forefootingEnd" in message:
            self.stage_signal.emit("fer_forefooting_end", self.fer.aggregateEmotions(), 0)

        elif "getEmotion_lyingStart" in message:
            self.stage_signal.emit("fer_lying_start", self.fer.aggregateEmotions(), 0)

        elif "getEmotion_lyingEnd" in message:
            self.stage_signal.emit("fer_lying_end", self.fer.aggregateEmotions(), 0)

        elif "getEmotion_exercise" in message:
            self.stage_signal.emit("fer_exercise", self.fer.aggregateEmotions(), 0)

        print(message, self.can_do_detection)

    def check_current_exercise(self) -> bool:
        ret, depth, frame = self.camera.get_frame()
        self.score_signal.emit(False)

        if not ret:
            return False

        landmarks = self.get_pose_estimation_landmarks(frame)

        if not landmarks:
            # print("No landmarks")
            return False

        self.exercise_interrupt_signal.emit()

        if landmarks and self.current_exercise.exercise_lock is False:
            self.current_exercise.do_check_exercise(landmarks, self.stage_signal, self.exercise_label_signal,
                                                    self.score_signal, depth)
        return True

    def calculate_distance(self, point1, point2):
        """
        Calculate the Euclidean distance between two points.

        Args:
            point1 (tuple): Coordinates of the first point as (x, y).
            point2 (tuple): Coordinates of the second point as (x, y).

        Returns:
            float: Euclidean distance between the two points.
        """
        x1, y1 = point1
        x2, y2 = point2
        distance = math.sqrt((x1 - x2) ** 2 + (y1 - y2) ** 2)
        return distance

    def get_pose_estimation_landmarks(self, frame):
        results = self.mp_pose.process(frame)
        # print("results",results.pose_landmarks)
        return results.pose_landmarks

    def get_nose_distance_coordinates(self, frame, depth):
        landmarks = self.get_pose_estimation_landmarks(frame)

        distance, nose_coordinates = 0, (0, 0)
        # Get the x and y coordinates of the nose to tuple
        if landmarks:
            nose_landmark = landmarks.landmark[mp.solutions.pose.PoseLandmark.NOSE.value]

            if nose_landmark.visibility < 0.65:
                return distance, nose_coordinates

            nose = [
                nose_landmark.x,
                nose_landmark.y
            ]

            frame_width, frame_height = frame.shape[1], frame.shape[0]
            nose_coordinates = tuple(
                np.multiply(nose, [frame_width, frame_height]).astype(int))

            # Ensure coordinates are within the bounds of the 'depth' array
            nose_coordinates = (
                min(nose_coordinates[0], frame_width - 1),
                min(nose_coordinates[1], frame_height - 1)
            )

            # Get the distance value from the 'depth' array using the nose coordinates
            if frame_width < 1920:
                distance = depth[nose_coordinates[1], nose_coordinates[0]]

        return distance, nose_coordinates

    def __del__(self) -> None:
        # Clean up the Mediapipe pose estimation
        if self.mp_pose:
            self.mp_pose.close()

    # def check_lift_right_leg_exercise(self):
    #     # Get frame
    #     ret, depth, frame = self.camera.get_frame()
    #     # Get the landmarks from the frame
    #     landmarks = self.get_pose_estimation_landmarks(frame)

    #     self.score_signal.emit(False)
