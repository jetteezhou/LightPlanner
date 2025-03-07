

def wipe_down(center_point, HOME_POSE_D, Arm, Gripper, pick_horizon=False, HOME_POSE_H=None):
    assert (pick_horizon is True and HOME_POSE_H is not None) or \
        (pick_horizon is False), "pick_horizon should get a HOME_POSE_H"
    x_base = center_point[0]
    y_base = center_point[1]
    z_base = center_point[2]
    Arm.movel(HOME_POSE_D)
    Arm.movel([HOME_POSE_D[0]-x_base, HOME_POSE_D[1]-y_base, HOME_POSE_D[2]-z_base+0.10, HOME_POSE_D[3], HOME_POSE_D[4], HOME_POSE_D[5]])
    Arm.movel([HOME_POSE_D[0]-x_base, HOME_POSE_D[1]-y_base, HOME_POSE_D[2]-z_base+0.03, HOME_POSE_D[3], HOME_POSE_D[4], HOME_POSE_D[5]])
    Arm.movel([HOME_POSE_D[0]-x_base+0.05, HOME_POSE_D[1]-y_base, HOME_POSE_D[2]-z_base+0.03, HOME_POSE_D[3], HOME_POSE_D[4], HOME_POSE_D[5]])
    Arm.movel([HOME_POSE_D[0]-x_base-0.05, HOME_POSE_D[1]-y_base, HOME_POSE_D[2]-z_base+0.03, HOME_POSE_D[3], HOME_POSE_D[4], HOME_POSE_D[5]])
    Arm.movel([HOME_POSE_D[0]-x_base, HOME_POSE_D[1]-y_base, HOME_POSE_D[2]-z_base+0.10, HOME_POSE_D[3], HOME_POSE_D[4], HOME_POSE_D[5]])
    Gripper.open()
    if pick_horizon:
        Arm.movel(HOME_POSE_H)
    else:
        Arm.movel(HOME_POSE_D)
    return 'Successful!'