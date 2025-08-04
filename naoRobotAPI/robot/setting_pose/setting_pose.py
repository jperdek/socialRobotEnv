import os
from naoqi import ALProxy

import dotenv

if os.environ.get("LOCAL", "True") == "True":
    dotenv.load_dotenv()


def set_nao_pose(angles_dict):
    NAO_IP = os.environ.get("NAO_IP", "127.0.0.1")
    NAO_PORT = int(os.environ.get("NAO_PORT", 9559))
    nao_motion = ALProxy("ALMotion", NAO_IP, NAO_PORT)

    nao_motion.stiffnessInterpolation("Body", 1.0, 1.0)

    # Define joints and their T-pose angles (in radians)
    joints = [
        # Arms
        "LShoulderPitch", "LShoulderRoll", "LElbowRoll", "LElbowYaw", "LWristYaw",
        "RShoulderPitch", "RShoulderRoll", "RElbowRoll", "RElbowYaw", "RWristYaw",
        # Legs in stable position
        "LHipRoll", "LHipPitch", "LKneePitch", "LAnklePitch", "LAnkleRoll",
        "RHipRoll", "RHipPitch", "RKneePitch", "RAnklePitch", "RAnkleRoll",
        # Head straight
        "HeadYaw", "HeadPitch"
    ]

    angles = [
        # Left Arm (straight out to side)
        angles_dict["LShoulderPitch"],
        angles_dict["LElbowRoll"],
        angles_dict["LElbowYaw"],
        angles_dict["LWristYaw"],
        # Right Arm (straight out to side)
        angles_dict["RShoulderPitch"],
        #angles_dict[""],
        angles_dict["RElbowRoll"],
        angles_dict["RElbowYaw"],
        angles_dict["RWristYaw"],
        # Legs (stable standing position)
        angles_dict["LHipRoll"],
        angles_dict["LHipPitch"],
        angles_dict["LKneePitch"],
        angles_dict["LAnklePitch"],
        angles_dict["LAnkleRoll"],
        angles_dict["RHipRoll"],
        angles_dict["RHipPitch"],
        angles_dict["RKneePitch"],
        angles_dict["RAnklePitch"],
        angles_dict["RAnkleRoll"],
        # Head (facing forward)
        angles_dict["HeadYaw"],
        angles_dict["HeadPitch"]
    ]

    duration = 3.0
    # Create time list (all joints will move simultaneously)
    times = [duration] * len(joints)

    # Execute the movement - this will block until movement is complete
    nao_motion.angleInterpolation(joints, angles, times, True)
