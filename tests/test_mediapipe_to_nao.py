import math
import requests

MEDIA_PIPE_URL = "http://127.0.0.1:6001/media_pipe_pose/pose_from_image"
SET_POSE_URL   = "http://127.0.0.1:5000/setting_pose/setPose"

def get_pose_from_image(path="/images/test_pose.jpg"):
    resp = requests.get(MEDIA_PIPE_URL, params={"file_location": path})
    resp.raise_for_status()
    return resp.json()

def angle_between(v1, v2):
    """Return angle between two 3D vectors."""
    import numpy as np
    v1 = np.array(v1, dtype=float)
    v2 = np.array(v2, dtype=float)
    n1 = np.linalg.norm(v1)
    n2 = np.linalg.norm(v2)
    if n1 == 0 or n2 == 0:
        return 0.0
    cos_a = float((v1 @ v2) / (n1 * n2))
    cos_a = max(-1.0, min(1.0, cos_a))  # clamp for numerical safety
    return math.acos(cos_a)

def mediapipe_to_nao_angles(mp_pose: dict):
    """
    Very crude mapping: only try to estimate shoulders + elbows.
    Everything else = 0.0.
    This is for TESTING the pipeline, not anatomically correct imitation.
    """

    def p(name):
        return mp_pose[name]["x"], mp_pose[name]["y"], mp_pose[name]["z"]

    # Convenience vectors
    def vec(a, b):
        return (b[0] - a[0], b[1] - a[1], b[2] - a[2])

    import numpy as np

    # Left side points
    L_sh = p("Left shoulder")
    L_el = p("Left elbow")
    L_wr = p("Left wrist")
    L_hip = p("Left hip")

    # Right side points
    R_sh = p("Right shoulder")
    R_el = p("Right elbow")
    R_wr = p("Right wrist")
    R_hip = p("Right hip")

    # ----- SHOULDER PITCH (rough) -----
    # Use vertical + depth difference between shoulder and elbow.
    # y: top->bottom, z: towards camera (negative).
    # We just cook some atan2 to get something that moves when the arm moves.
    def shoulder_pitch(sh, el, sign=1.0):
        dy = el[1] - sh[1]
        dz = el[2] - sh[2]
        # negate because NAO convention is different from image; this is *approx*
        return sign * math.atan2(-dy, -dz)

    # ----- SHOULDER ROLL (rough) -----
    # Use sidewards movement: x difference between shoulder and elbow.
    # x: left->right; 0.5 is middle in your example.
    def shoulder_roll(sh, el, side="L"):
        dx = el[0] - sh[0]
        dy = el[1] - sh[1]
        ang = math.atan2(dx, abs(dy) + 1e-6)
        # For NAO: left roll positive when lifting arm to the side,
        # right roll negative – we just enforce that sign convention.
        return ang if side == "L" else -ang

    # ----- ELBOW ROLL (rough bend angle) -----
    def elbow_roll(sh, el, wr, side="L"):
        upper = vec(sh, el)
        fore = vec(el, wr)
        ang_at_elbow = angle_between(upper, fore)   # ~pi when straight
        roll = math.pi - ang_at_elbow              # 0 when straight, >0 when bent
        if side == "R":
            roll = -roll
        return roll

    # For yaw we just set 0.0 – one view is not enough to estimate it reliably.
    LShoulderPitch = shoulder_pitch(L_sh, L_el, sign=1.0)
    RShoulderPitch = shoulder_pitch(R_sh, R_el, sign=1.0)

    LShoulderRoll  = shoulder_roll(L_sh, L_el, side="L")
    RShoulderRoll  = shoulder_roll(R_sh, R_el, side="R")

    LElbowRoll     = elbow_roll(L_sh, L_el, L_wr, side="L")
    RElbowRoll     = elbow_roll(R_sh, R_el, R_wr, side="R")

    LElbowYaw      = 0.0
    RElbowYaw      = 0.0
    LWristYaw      = 0.0
    RWristYaw      = 0.0

    # Legs, hips, head = 0.0 for now
    LHipRoll = LHipPitch = LKneePitch = LAnklePitch = LAnkleRoll = 0.0
    RHipRoll = RHipPitch = RKneePitch = RAnklePitch = RAnkleRoll = 0.0
    HeadYaw = HeadPitch = 0.0

    # IMPORTANT: order must match your `joints` list in set_nao_pose
    angles = [
        LShoulderPitch, LShoulderRoll, LElbowRoll, LElbowYaw, LWristYaw,
        RShoulderPitch, RShoulderRoll, RElbowRoll, RElbowYaw, RWristYaw,
        LHipRoll, LHipPitch, LKneePitch, LAnklePitch, LAnkleRoll,
        RHipRoll, RHipPitch, RKneePitch, RAnklePitch, RAnkleRoll,
        HeadYaw, HeadPitch,
    ]

    # Optionally clamp to NAO's joint limits here if needed.

    return angles

def send_angles_to_nao(angles):
    resp = requests.post(SET_POSE_URL, json={"angles": angles})
    resp.raise_for_status()
    return resp.json()

def main():
    print("1) Getting Mediapipe pose from image...")
    pose = get_pose_from_image("/images/arm.jpg")

    print("2) Converting Mediapipe landmarks to NAO joint angles...")
    angles = mediapipe_to_nao_angles(pose)
    print("Angles:", angles)

    print("3) Sending angles to NAO via /setting_pose/setPose...")
    result = send_angles_to_nao(angles)
    print("Result:", result)

if __name__ == "__main__":
    main()
