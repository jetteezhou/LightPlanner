

def pick_down(center_point, HOME_POSE_D, Arm, Gripper):
    x_base = center_point[0]
    y_base = center_point[1]
    z_base = center_point[2]
    Arm.movel(HOME_POSE_D)
    Arm.movel([HOME_POSE_D[0]-x_base, HOME_POSE_D[1]+y_base, HOME_POSE_D[2]-z_base+0.1, HOME_POSE_D[3], HOME_POSE_D[4], HOME_POSE_D[5]])
    Arm.movel([HOME_POSE_D[0]-x_base, HOME_POSE_D[1]+y_base, HOME_POSE_D[2]-z_base    , HOME_POSE_D[3], HOME_POSE_D[4], HOME_POSE_D[5]])
    Gripper.close()
    Arm.movel(HOME_POSE_D)
    return "Successful!"
    

def pick_horizon(center_point, HOME_POSE_H, Arm, Gripper, put_down=False, HOME_POSE_D=None):
    assert (put_down is True and HOME_POSE_D is not None) or \
        (put_down is False), "put_down should get a HOME_POSE_D"
    x_base = center_point[0]
    z_base = center_point[1]
    y_base = center_point[2]
    Arm.movel(HOME_POSE_H)
    Arm.movel([HOME_POSE_H[0]-x_base, HOME_POSE_H[1]-y_base+0.105, HOME_POSE_H[2]-z_base, HOME_POSE_H[3], HOME_POSE_H[4], HOME_POSE_H[5]])
    Arm.movel([HOME_POSE_H[0]-x_base, HOME_POSE_H[1]-y_base,       HOME_POSE_H[2]-z_base, HOME_POSE_H[3], HOME_POSE_H[4], HOME_POSE_H[5]])
    Gripper.close()
    Arm.movel([HOME_POSE_H[0]-x_base, HOME_POSE_H[1]-y_base+0.13,  HOME_POSE_H[2]-z_base+0.05, HOME_POSE_H[3], HOME_POSE_H[4], HOME_POSE_H[5]])
    if put_down:
        Arm.movel(HOME_POSE_D)
    else:
        Arm.movel(HOME_POSE_H)
    return "Successful!"