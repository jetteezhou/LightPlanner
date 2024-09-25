

def put_down(center_point, HOME_POSE_D, Arm, Gripper, pick_horizon=False, HOME_POSE_H=None):
    assert (pick_horizon is True and HOME_POSE_H is not None) or \
        (pick_horizon is False), "pick_horizon should get a HOME_POSE_H"
    x_base = center_point[0]
    y_base = center_point[1]
    z_base = center_point[2]
    Arm.movel(HOME_POSE_D)
    Arm.movel([HOME_POSE_D[0]-x_base, HOME_POSE_D[1]+y_base, HOME_POSE_D[2]-z_base+0.1,   0.16, 3.10, -0.0])
    Arm.movel([HOME_POSE_D[0]-x_base, HOME_POSE_D[1]+y_base, HOME_POSE_D[2]-z_base+0.035, 0.16, 3.10, -0.0])
    Gripper.open()
    Arm.movel([HOME_POSE_D[0]-x_base, HOME_POSE_D[1]+y_base, HOME_POSE_D[2]-z_base+0.1,   0.16, 3.10, -0.0])
    if pick_horizon:
        Arm.movel(HOME_POSE_H)
    else:
        Arm.movel(HOME_POSE_D)
    return "success"