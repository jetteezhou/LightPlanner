
def close_horizon(center_point, HOME_POSE_H, Arm, Gripper):
    x_base = center_point[0]
    z_base = center_point[1]
    y_base = center_point[2]
    Arm.movel(HOME_POSE_H)
    Arm.movel([HOME_POSE_H[0]-x_base, HOME_POSE_H[1]-y_base+0.075, HOME_POSE_H[2]-z_base, HOME_POSE_H[3], HOME_POSE_H[4], HOME_POSE_H[5]])
    Gripper.close()
    Arm.movel([HOME_POSE_H[0]-x_base, HOME_POSE_H[1]-y_base-0.03,  HOME_POSE_H[2]-z_base, HOME_POSE_H[3], HOME_POSE_H[4], HOME_POSE_H[5]])
    Arm.movel([HOME_POSE_H[0]-x_base, HOME_POSE_H[1]-y_base+0.10,  HOME_POSE_H[2]-z_base, HOME_POSE_H[3], HOME_POSE_H[4], HOME_POSE_H[5]])
    Gripper.open()
    Arm.movel(HOME_POSE_H)
    return 'Successful!'