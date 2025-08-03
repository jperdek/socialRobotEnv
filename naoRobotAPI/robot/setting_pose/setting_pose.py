import dotenv

if os.environ.get("LOCAL", "True") == "True":
    dotenv.load_dotenv()




def set_nao_pose(angles_dict):
    NAO_IP = os.environ.get("NAO_IP", "127.0.0.1")
    NAO_PORT = int(os.environ.get("NAO_PORT", 9559))
    nao_motion = ALProxy("ALMotion", ip, port)


    motion.stiffnessInterpolation("Body", 1.0, 1.0)

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
        0.0,  # LShoulderPitch (0 = straight out)
        1.57,
        0.0,  # LElbowRoll
        0.0,  # LElbowYaw
        0.0,  # LWristYaw
        # Right Arm (straight out to side)
        0.0,  # RShoulderPitch
        -1.57,
        0.0,  # RElbowRoll
        0.0,  # RElbowYaw
        0.0,  # RWristYaw
        # Legs (stable standing position)
        0.0,  # LHipRoll
        0.0,  # LHipPitch
        0.0,  # LKneePitch
        0.0,  # LAnklePitch
        0.0,  # LAnkleRoll
        0.0,  # RHipRoll
        0.0,  # RHipPitch
        0.0,  # RKneePitch
        0.0,  # RAnklePitch
        0.0,  # RAnkleRoll
        # Head (facing forward)
        0.0,  # HeadYaw
        0.0  # HeadPitch
    ]

    # Create time list (all joints will move simultaneously)
    times = [duration] * len(joints)

    # Execute the movement - this will block until movement is complete
    motion.angleInterpolation(joints, angles, times, True)
