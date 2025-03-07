import numpy as np

# 相机相对于工具的旋转矩阵 (无旋转差异，单位矩阵)
R_C_to_T = np.eye(3)
# 相机相对于工具的平移向量 
t_C_to_T = np.array([-0.038, -0.065, -0.135])


def camera_to_tool(P_C, R_C_to_T=R_C_to_T, t_C_to_T=t_C_to_T):
    P_C = np.array(P_C)
    return np.dot(R_C_to_T, P_C) + t_C_to_T