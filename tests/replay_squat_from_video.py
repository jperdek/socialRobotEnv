import math
import time
import requests
import numpy as np

MEDIA_PIPE_VIDEO_URL = "http://127.0.0.1:6001/media_pipe_pose/pose_from_video"
SET_POSE_URL         = "http://127.0.0.1:5000/setting_pose/setPose"

VIDEO_PATH           = "/images/squat_mini.mp4"
FRAMES_PER_SEC       = 1        # how many frames per second to sample from video
DELAY_BETWEEN_FRAMES = 3.5      # seconds; should be >= duration in set_nao_pose (3.0)


def angle_between(v1, v2):
    """Return angle between two 3D vectors in radians."""
    v1 = np.array(v1, dtype=float)
    v2 = np.array(v2, dtype=float)
    n1 = np.linalg.norm(v1)
    n2 = np.linalg.norm(v2)
    if n1 == 0 or n2 == 0:
        return 0.0
    cos_a = float((v1 @ v2) / (n1 * n2))
    cos_a = max(-1.0, min(1.0, cos_a))  # clamp
    return math.acos(cos_a)


def mediapipe_to_nao_angles(mp_pose: dict):
    """
    Convert Mediapipe landmarks (one frame) into NAO joint angles.

    Assumptions:
    - Mediapipe Pose coordinates are camera-relative, x ~ left/right, y ~ up/down (image),
      z ~ depth (negative forward). We treat them consistently but this is heuristic.
    - We mostly work with relative vectors and angles between segments.
    - NAO joint limits are approximated and used just to clamp extreme values.

    Returns list of 22 joint angles (radians) in this order:

    [
      LShoulderPitch, LShoulderRoll, LElbowRoll, LElbowYaw, LWristYaw,
      RShoulderPitch, RShoulderRoll, RElbowRoll, RElbowYaw, RWristYaw,
      LHipRoll, LHipPitch, LKneePitch, LAnklePitch, LAnkleRoll,
      RHipRoll, RHipPitch, RKneePitch, RAnklePitch, RAnkleRoll,
      HeadYaw, HeadPitch
    ]
    """

    def p(name):
        v = mp_pose.get(name)
        if not v or isinstance(v, str):
            raise KeyError(name)
        return v["x"], v["y"], v["z"]

    def vec(a, b):
        return (b[0] - a[0], b[1] - a[1], b[2] - a[2])

    def v_add(a, b):
        return (a[0] + b[0], a[1] + b[1], a[2] + b[2])

    def v_scale(a, s):
        return (a[0] * s, a[1] * s, a[2] * s)

    def angle_between(v1, v2):
        v1 = np.array(v1, dtype=float)
        v2 = np.array(v2, dtype=float)
        n1 = np.linalg.norm(v1)
        n2 = np.linalg.norm(v2)
        if n1 == 0 or n2 == 0:
            return 0.0
        cos_a = float((v1 @ v2) / (n1 * n2))
        cos_a = max(-1.0, min(1.0, cos_a))
        return math.acos(cos_a)

    def clamp(x, lo, hi):
        return max(lo, min(hi, x))

    # --- approximate NAO joint limits (radians) ---
    # (values are "ballpark good enough" for safety; tune if needed)
    LIMITS = {
        "LShoulderPitch": (-2.08, 2.08),
        "RShoulderPitch": (-2.08, 2.08),
        "LShoulderRoll":  (0.01, 1.56),
        "RShoulderRoll":  (-1.56, -0.01),
        "LElbowYaw":      (-2.08, 2.08),
        "RElbowYaw":      (-2.08, 2.08),
        "LElbowRoll":     (-1.56, -0.01),
        "RElbowRoll":     (0.01, 1.56),
        "LWristYaw":      (-1.82, 1.82),
        "RWristYaw":      (-1.82, 1.82),

        "LHipRoll":       (-0.39, 0.79),
        "RHipRoll":       (-0.79, 0.39),
        "LHipPitch":      (-1.04, 0.48),
        "RHipPitch":      (-1.04, 0.48),
        "LKneePitch":     (-0.09, 2.11),
        "RKneePitch":     (-0.09, 2.11),
        "LAnklePitch":    (-1.19, 0.92),
        "RAnklePitch":    (-1.19, 0.92),
        "LAnkleRoll":     (-0.39, 0.79),
        "RAnkleRoll":     (-0.79, 0.39),

        "HeadYaw":        (-2.08, 2.08),
        "HeadPitch":      (-0.67, 0.51),
    }

    # default all angles to 0
    LShoulderPitch = LShoulderRoll = LElbowRoll = LElbowYaw = LWristYaw = 0.0
    RShoulderPitch = RShoulderRoll = RElbowRoll = RElbowYaw = RWristYaw = 0.0

    LHipRoll = LHipPitch = LKneePitch = LAnklePitch = LAnkleRoll = 0.0
    RHipRoll = RHipPitch = RKneePitch = RAnklePitch = RAnkleRoll = 0.0

    HeadYaw = HeadPitch = 0.0

    # ========== UPPER BODY ==========
    try:
        L_sh = p("Left shoulder")
        L_el = p("Left elbow")
        L_wr = p("Left wrist")
        R_sh = p("Right shoulder")
        R_el = p("Right elbow")
        R_wr = p("Right wrist")

        # neck as midpoint of shoulders (used later as well)
        neck = v_scale(v_add(L_sh, R_sh), 0.5)

        # 1) Shoulder pitch (forward/back) – use vertical & depth differences
        def shoulder_pitch(sh, el):
            dy = el[1] - sh[1]   # image y (down is +)
            dz = el[2] - sh[2]   # depth
            # hands up => smaller y (screen up), so we flip sign to be intuitive
            return math.atan2(-dy, -dz)

        # 2) Shoulder roll (outward) – use sideways relative to vertical
        def shoulder_roll(sh, el, side="L"):
            dx = el[0] - sh[0]   # left/right
            dy = el[1] - sh[1]
            ang = math.atan2(dx, abs(dy) + 1e-6)
            return ang if side == "L" else -ang

        # 3) Elbow roll – angle at elbow between upper arm and forearm
        def elbow_roll(sh, el, wr, side="L"):
            upper = vec(sh, el)
            fore  = vec(el, wr)
            ang_at_elbow = angle_between(upper, fore)   # ~pi straight
            roll = math.pi - ang_at_elbow              # 0 straight, >0 bent
            if side == "R":
                roll = -roll
            return roll

        # 4) Elbow yaw – rotation around the upper-arm axis.
        #    Approximate using azimuth of forearm in horizontal (x,z) plane
        #    relative to upper arm.
        def elbow_yaw(sh, el, wr, side="L"):
            upper = vec(sh, el)
            fore  = vec(el, wr)

            # project to horizontal plane (x,z)
            upper_h = (upper[0], 0.0, upper[2])
            fore_h  = (fore[0], 0.0, fore[2])

            if np.linalg.norm(upper_h) == 0 or np.linalg.norm(fore_h) == 0:
                return 0.0

            ang = angle_between(upper_h, fore_h)

            # sign using cross product wrt "up" axis (y)
            ux, _, uz = upper_h
            fx, _, fz = fore_h
            cross_y = ux * fz - uz * fx
            if side == "L":
                if cross_y < 0:
                    ang = -ang
            else:
                # right side mirror
                if cross_y > 0:
                    ang = -ang
            return ang

        # 5) Wrist yaw – we don't have true orientation, but we can
        #    approximate from wrist->index vs wrist->elbow direction.
        def wrist_yaw(el, wr, hand, side="L"):
            forearm = vec(el, wr)
            hand_v  = vec(wr, hand)

            fore_h = (forearm[0], 0.0, forearm[2])
            hand_h = (hand_v[0], 0.0, hand_v[2])
            if np.linalg.norm(fore_h) == 0 or np.linalg.norm(hand_h) == 0:
                return 0.0

            ang = angle_between(fore_h, hand_h)
            # sign similar to elbow yaw
            fx, _, fz = fore_h
            hx, _, hz = hand_h
            cross_y = fx * hz - fz * hx
            if side == "L":
                if cross_y < 0:
                    ang = -ang
            else:
                if cross_y > 0:
                    ang = -ang
            # scale down a bit to not over-rotate
            return 0.7 * ang

        # try to use "index" landmarks for hand direction if they exist
        try:
            L_hand = p("Left index")
            R_hand = p("Right index")
        except KeyError:
            # if not, fall back to wrist direction only (no extra yaw)
            L_hand = L_wr
            R_hand = R_wr

        # compute angles
        LShoulderPitch = shoulder_pitch(L_sh, L_el)
        RShoulderPitch = shoulder_pitch(R_sh, R_el)

        LShoulderRoll  = shoulder_roll(L_sh, L_el, side="L")
        RShoulderRoll  = shoulder_roll(R_sh, R_el, side="R")

        LElbowRoll     = elbow_roll(L_sh, L_el, L_wr, side="L")
        RElbowRoll     = elbow_roll(R_sh, R_el, R_wr, side="R")

        LElbowYaw      = elbow_yaw(L_sh, L_el, L_wr, side="L")
        RElbowYaw      = elbow_yaw(R_sh, R_el, R_wr, side="R")

        LWristYaw      = wrist_yaw(L_el, L_wr, L_hand, side="L")
        RWristYaw      = wrist_yaw(R_el, R_wr, R_hand, side="R")

    except KeyError:
        # if any upper-body joint is missing, keep arms neutral
        neck = None

    # ========== LOWER BODY ==========
    try:
        L_hip  = p("Left hip")
        L_knee = p("Left knee")
        L_ank  = p("Left ankle")
        L_foot = p("Left foot index")

        R_hip  = p("Right hip")
        R_knee = p("Right knee")
        R_ank  = p("Right ankle")
        R_foot = p("Right foot index")

        # pelvis center
        pelvis = v_scale(v_add(L_hip, R_hip), 0.5)

        # --- Left leg ---
        L_thigh = vec(L_hip, L_knee)
        L_shin  = vec(L_knee, L_ank)
        L_footv = vec(L_ank, L_foot)

        left_knee_angle  = angle_between(L_thigh, L_shin)   # ~pi straight
        left_ankle_angle = angle_between(L_shin, L_footv)

        # knee pitch: 0 straight, positive for bending
        LKneePitch   = max(0.0, 1.2 * (math.pi - left_knee_angle))  # up to ~2.5

        # ankle pitch: shin vs foot pitch, sign so that dorsiflexion is positive
        LAnklePitch  = -0.6 * (math.pi - left_ankle_angle)

        # hip pitch: angle between torso and thigh
        if neck is None:
            # if neck missing, approximate torso with pelvis-up vertical
            torso_L = vec(L_hip, v_add(L_hip, (0, -1, 0)))
        else:
            torso_L = vec(L_hip, neck)

        left_hip_angle = angle_between(torso_L, L_thigh)
        # pi/2 ~ neutral; more flexion => hip_angle > pi/2
        LHipPitch  = -0.7 * (left_hip_angle - math.pi/2)

        # --- Right leg ---
        R_thigh = vec(R_hip, R_knee)
        R_shin  = vec(R_knee, R_ank)
        R_footv = vec(R_ank, R_foot)

        right_knee_angle  = angle_between(R_thigh, R_shin)
        right_ankle_angle = angle_between(R_shin, R_footv)

        RKneePitch  = max(0.0, 1.2 * (math.pi - right_knee_angle))
        RAnklePitch = -0.6 * (math.pi - right_ankle_angle)

        if neck is None:
            torso_R = vec(R_hip, v_add(R_hip, (0, -1, 0)))
        else:
            torso_R = vec(R_hip, neck)

        right_hip_angle = angle_between(torso_R, R_thigh)
        RHipPitch  = -0.7 * (right_hip_angle - math.pi/2)

        # Hip roll – from lateral offset of hips relative to pelvis center
        LHipRoll = (L_hip[0] - pelvis[0]) * 1.0
        RHipRoll = (R_hip[0] - pelvis[0]) * 1.0

        # Ankle roll – from lateral direction of foot wrt ankle
        def ankle_roll(ank, foot, side="L"):
            footv = vec(ank, foot)
            # compare horizontal X vs vertical Y to get some tilt
            dx = footv[0]
            dy = footv[1]
            ang = math.atan2(dx, abs(dy) + 1e-6)
            return ang if side == "L" else -ang

        LAnkleRoll = ankle_roll(L_ank, L_foot, side="L")
        RAnkleRoll = ankle_roll(R_ank, R_foot, side="R")

    except KeyError:
        # legs neutral if something missing
        pass

    # ========== HEAD ==========
    try:
        nose = p("Nose")
    except KeyError:
        nose = None

    try:
        # use neck and pelvis if available
        if neck is None:
            L_sh = p("Left shoulder")
            R_sh = p("Right shoulder")
            neck = v_scale(v_add(L_sh, R_sh), 0.5)
        L_hip = p("Left hip")
        R_hip = p("Right hip")
        pelvis = v_scale(v_add(L_hip, R_hip), 0.5)
    except KeyError:
        neck = None
        pelvis = None

    if neck is not None and nose is not None:
        head_dir = vec(neck, nose)

        # Head yaw: horizontal rotation (look left/right)
        # atan2(x, z) – positive when looking to "camera left"
        HeadYaw = math.atan2(head_dir[0], -head_dir[2] + 1e-6)

        # Head pitch: up/down relative to torso
        HeadPitch = math.atan2(-head_dir[1], -head_dir[2] + 1e-6)

    # ========== CLAMP TO LIMITS ==========
    LShoulderPitch = clamp(LShoulderPitch, *LIMITS["LShoulderPitch"])
    RShoulderPitch = clamp(RShoulderPitch, *LIMITS["RShoulderPitch"])
    LShoulderRoll  = clamp(LShoulderRoll,  *LIMITS["LShoulderRoll"])
    RShoulderRoll  = clamp(RShoulderRoll,  *LIMITS["RShoulderRoll"])
    LElbowRoll     = clamp(LElbowRoll,     *LIMITS["LElbowRoll"])
    RElbowRoll     = clamp(RElbowRoll,     *LIMITS["RElbowRoll"])
    LElbowYaw      = clamp(LElbowYaw,      *LIMITS["LElbowYaw"])
    RElbowYaw      = clamp(RElbowYaw,      *LIMITS["RElbowYaw"])
    LWristYaw      = clamp(LWristYaw,      *LIMITS["LWristYaw"])
    RWristYaw      = clamp(RWristYaw,      *LIMITS["RWristYaw"])

    LHipRoll       = clamp(LHipRoll,       *LIMITS["LHipRoll"])
    RHipRoll       = clamp(RHipRoll,       *LIMITS["RHipRoll"])
    LHipPitch      = clamp(LHipPitch,      *LIMITS["LHipPitch"])
    RHipPitch      = clamp(RHipPitch,      *LIMITS["RHipPitch"])
    LKneePitch     = clamp(LKneePitch,     *LIMITS["LKneePitch"])
    RKneePitch     = clamp(RKneePitch,     *LIMITS["RKneePitch"])
    LAnklePitch    = clamp(LAnklePitch,    *LIMITS["LAnklePitch"])
    RAnklePitch    = clamp(RAnklePitch,    *LIMITS["RAnklePitch"])
    LAnkleRoll     = clamp(LAnkleRoll,     *LIMITS["LAnkleRoll"])
    RAnkleRoll     = clamp(RAnkleRoll,     *LIMITS["RAnkleRoll"])

    HeadYaw        = clamp(HeadYaw,        *LIMITS["HeadYaw"])
    HeadPitch      = clamp(HeadPitch,      *LIMITS["HeadPitch"])

    # final order must match your set_nao_pose joints list
    angles = [
        LShoulderPitch, LShoulderRoll, LElbowRoll, LElbowYaw, LWristYaw,
        RShoulderPitch, RShoulderRoll, RElbowRoll, RElbowYaw, RWristYaw,
        LHipRoll, LHipPitch, LKneePitch, LAnklePitch, LAnkleRoll,
        RHipRoll, RHipPitch, RKneePitch, RAnklePitch, RAnkleRoll,
        HeadYaw, HeadPitch,
    ]
    return angles



def get_video_poses(path: str):
    print(f"Requesting poses from video: {path}")
    resp = requests.get(
        MEDIA_PIPE_VIDEO_URL,
        params={
            "file_location": path,
            "number_frames_per_sec": FRAMES_PER_SEC,
        },
    )
    resp.raise_for_status()
    poses = resp.json()
    print(f"Received {len(poses)} frames from pose API.")
    return poses


def send_angles_to_nao(angles):
    resp = requests.post(SET_POSE_URL, json={"angles": angles})
    resp.raise_for_status()
    return resp.json()


def main():
    poses = get_video_poses(VIDEO_PATH)

    frame_index = 0
    for pose in poses:
        # skip frames with no detection
        if not pose:
            print(f"Frame {frame_index}: no landmarks, skipping.")
            frame_index += 1
            continue

        print(f"Frame {frame_index}: computing NAO angles...")
        angles = mediapipe_to_nao_angles(pose)
        print("  Angles:", [round(a, 3) for a in angles])

        print("  Sending to NAO...")
        result = send_angles_to_nao(angles)
        print("  Response:", result)

        # wait for robot to complete movement before next frame
        time.sleep(DELAY_BETWEEN_FRAMES)
        frame_index += 1

    print("Done replaying squat sequence.")


if __name__ == "__main__":
    main()
