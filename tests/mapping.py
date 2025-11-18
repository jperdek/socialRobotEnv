import math
import requests
import numpy as np

MEDIA_PIPE_URL = "http://127.0.0.1:6001/media_pipe_pose/pose_from_image"
SET_POSE_URL   = "http://127.0.0.1:5000/setting_pose/setPose"


def get_pose_from_image(path="/images/arm.jpg"):
    print(f"[DEBUG] Requesting Mediapipe pose for: {path}")
    resp = requests.get(MEDIA_PIPE_URL, params={"file_location": path})
    resp.raise_for_status()
    pose = resp.json()
    print("[DEBUG] Raw pose keys:", list(pose.keys()))
    return pose


# ----------------- HELPERS -----------------

def _vec(p):
    return np.array([p["x"], p["y"], p["z"]], dtype=float)

def _normalize(v):
    n = np.linalg.norm(v)
    return v if n == 0 else v / n


# Mediapipe coordinate frame
E_RIGHT = np.array([1, 0, 0])     # image right
E_UP    = np.array([0,-1, 0])     # image up
E_FRONT = np.array([0, 0,-1])     # toward camera


# ------------------------------------------------------
#               ARM ANGLE COMPUTATION
# ------------------------------------------------------

def _compute_arm_angles(shoulder, elbow, wrist, is_left):

    side_name = "LEFT" if is_left else "RIGHT"
    print(f"\n[DEBUG] ===== {side_name} ARM =====")

    print(f"[DEBUG] {side_name} shoulder raw: {shoulder}")
    print(f"[DEBUG] {side_name} elbow    raw: {elbow}")
    print(f"[DEBUG] {side_name} wrist    raw: {wrist}")

    sh = _vec(shoulder)
    el = _vec(elbow)
    wr = _vec(wrist)

    print(f"[DEBUG] {side_name} shoulder vec: {sh}")
    print(f"[DEBUG] {side_name} elbow    vec: {el}")
    print(f"[DEBUG] {side_name} wrist    vec: {wr}")

    # Upper & lower arm vectors
    u = _normalize(el - sh)       # upper arm
    v = _normalize(wr - el)       # forearm

    print(f"[DEBUG] {side_name} upper arm u: {u}")
    print(f"[DEBUG] {side_name} forearm  v: {v}")

    # -------------------------------------------------
    # SHOULDER PITCH  (forward/back)
    # -------------------------------------------------
    u_sag = u - np.dot(u, E_RIGHT) * E_RIGHT
    u_sag = _normalize(u_sag)
    print(f"[DEBUG] {side_name} u_sag (sagittal proj): {u_sag}")

    shoulder_pitch = math.atan2(
        -np.dot(u_sag, E_FRONT),     # forward/back
        -np.dot(u_sag, E_UP)         # up/down
    )
    print(f"[DEBUG] {side_name} shoulder_pitch (rad): {shoulder_pitch}")
    print(f"[DEBUG] {side_name} shoulder_pitch (deg): {math.degrees(shoulder_pitch)}")

    # -------------------------------------------------
    # SHOULDER ROLL (side raise)
    # -------------------------------------------------
    u_front = u - np.dot(u, E_FRONT) * E_FRONT
    u_front = _normalize(u_front)
    print(f"[DEBUG] {side_name} u_front (frontal proj): {u_front}")

    side = +1 if is_left else -1

    shoulder_roll = math.atan2(
        side * np.dot(u_front, E_RIGHT),
        -np.dot(u_front, E_UP)
    )
    print(f"[DEBUG] {side_name} shoulder_roll (rad): {shoulder_roll}")
    print(f"[DEBUG] {side_name} shoulder_roll (deg): {math.degrees(shoulder_roll)}")

    # -------------------------------------------------
    # ELBOW ROLL (flexion)
    # -------------------------------------------------
    cos_val = float(np.dot(u, v))
    cos_val_clamped = max(-1.0, min(1.0, cos_val))
    theta = math.acos(cos_val_clamped)

    print(f"[DEBUG] {side_name} elbow cos(u·v): {cos_val} (clamped {cos_val_clamped})")
    print(f"[DEBUG] {side_name} elbow theta raw (rad): {theta}")
    print(f"[DEBUG] {side_name} elbow theta raw (deg): {math.degrees(theta)}")

    if theta < math.radians(25):
        print(f"[DEBUG] {side_name} elbow within deadzone (<25 deg) -> set to 0")
        theta = 0.0

    elbow_roll = (+1 if is_left else -1) * theta
    elbow_roll = np.clip(elbow_roll, -1.56, 1.56)

    print(f"[DEBUG] {side_name} elbow_roll (rad): {elbow_roll}")
    print(f"[DEBUG] {side_name} elbow_roll (deg): {math.degrees(elbow_roll)}")

    # -------------------------------------------------
    # ELBOW YAW (forearm twist)
    # -------------------------------------------------
    ref = _normalize(np.cross(E_UP, u))
    if np.linalg.norm(ref) < 1e-6:
        ref = _normalize(np.cross(E_RIGHT, u))

    print(f"[DEBUG] {side_name} ref for yaw: {ref}")

    proj_f = v - np.dot(v, u) * u
    proj_f = _normalize(proj_f)
    print(f"[DEBUG] {side_name} proj_f (forearm proj for yaw): {proj_f}")

    dot_y = float(np.dot(proj_f, ref))
    dot_y_clamped = max(-1.0, min(1.0, dot_y))
    yaw_angle = math.acos(dot_y_clamped)

    print(f"[DEBUG] {side_name} yaw dot(proj_f, ref): {dot_y} (clamped {dot_y_clamped})")
    print(f"[DEBUG] {side_name} yaw_angle raw (rad): {yaw_angle}")
    print(f"[DEBUG] {side_name} yaw_angle raw (deg): {math.degrees(yaw_angle)}")

    cross_y = np.cross(ref, proj_f)
    sign_y = np.sign(np.dot(cross_y, u))
    elbow_yaw = sign_y * yaw_angle

    print(f"[DEBUG] {side_name} yaw sign_y: {sign_y}")
    print(f"[DEBUG] {side_name} elbow_yaw before L-flip (rad): {elbow_yaw}")
    print(f"[DEBUG] {side_name} elbow_yaw before L-flip (deg): {math.degrees(elbow_yaw)}")

    # FINAL FIX: Left yaw must be flipped
    if is_left:
        elbow_yaw = -elbow_yaw
        print(f"[DEBUG] {side_name} elbow_yaw flipped for LEFT")

    elbow_yaw = np.clip(elbow_yaw, -2.0, 2.0)

    print(f"[DEBUG] {side_name} elbow_yaw final (rad): {elbow_yaw}")
    print(f"[DEBUG] {side_name} elbow_yaw final (deg): {math.degrees(elbow_yaw)}")

    print(f"[DEBUG] {side_name} FINAL ANGLES (deg): "
          f"pitch={math.degrees(shoulder_pitch):.2f}, "
          f"roll={math.degrees(shoulder_roll):.2f}, "
          f"elbow_roll={math.degrees(elbow_roll):.2f}, "
          f"elbow_yaw={math.degrees(elbow_yaw):.2f}")

    return shoulder_pitch, shoulder_roll, elbow_yaw, elbow_roll



# ------------------------------------------------------
#             PUBLIC MAPPING FUNCTION
# ------------------------------------------------------

def mediapipe_to_nao_arm_angles(mp_pose):

    print("\n[DEBUG] === USING THESE LANDMARKS FROM MEDIAPIPE ===")
    for name in ["Left shoulder", "Left elbow", "Left wrist",
                 "Right shoulder", "Right elbow", "Right wrist"]:
        if name in mp_pose:
            print(f"[DEBUG] {name}: {mp_pose[name]}")
        else:
            print(f"[DEBUG] {name}: MISSING in pose dict!")

    LSp, LSr, LEy, LEr = _compute_arm_angles(
        mp_pose["Left shoulder"], mp_pose["Left elbow"], mp_pose["Left wrist"], True
    )

    RSp, RSr, REy, REr = _compute_arm_angles(
        mp_pose["Right shoulder"], mp_pose["Right elbow"], mp_pose["Right wrist"], False
    )

    # NAO rule: mirror ONLY shoulder roll
    RSr = -RSr

    LWY = 0.0
    RWY = 0.0

    angles = [
        LSp, LSr, LEr, LEy, LWY,
        RSp, RSr, REr, REy, RWY,
        0,0,0,0,0, 0,0,0,0,0, 0,0
    ]

    print("\n[DEBUG] === FINAL ANGLES SENT TO NAO (radians) ===")
    joint_names = [
        "LShoulderPitch","LShoulderRoll","LElbowRoll","LElbowYaw","LWristYaw",
        "RShoulderPitch","RShoulderRoll","RElbowRoll","RElbowYaw","RWristYaw",
        "LHipRoll","LHipPitch","LKneePitch","LAnklePitch","LAnkleRoll",
        "RHipRoll","RHipPitch","RKneePitch","RAnklePitch","RAnkleRoll",
        "HeadYaw","HeadPitch"
    ]
    for name, val in zip(joint_names, angles):
        print(f"[DEBUG] {name}: {val:.4f} rad ({math.degrees(val):.2f} deg)")

    return angles



def send_angles_to_nao(angles):
    print("\n[DEBUG] Posting angles to NAO...")
    resp = requests.post(SET_POSE_URL, json={"angles": angles})
    print("[DEBUG] NAO response status:", resp.status_code)
    resp.raise_for_status()
    print("[DEBUG] NAO response JSON:", resp.json())
    return resp.json()


def main():
    print("1) Getting Mediapipe pose...")
    pose = get_pose_from_image()

    print("\n2) Computing angles...")
    angles = mediapipe_to_nao_arm_angles(pose)

    print("\n3) Sending to NAO...")
    result = send_angles_to_nao(angles)

    print("\nResult:", result)


if __name__ == "__main__":
    main()
