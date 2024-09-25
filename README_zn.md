# UniPlanner: An Efficient and Unified Embodied Task Planner for Edge Devices

![Overview of UniPlanner](./images/framework.png)


## Overview

**UniPlanner** is a task planner that reduces the high latency and computational costs of large language models (LLMs). Instead of using multiple agents for subtask planning and control, it uses a single lightweight LLM to handle everything in one context until the task is complete. This reduces system complexity and avoids the need for communication with cloud servers, lowering latency. UniPlanner performs efficiently on devices like the **Jetson Xavier Orin**, making it ideal for low-resource environments.

### Features:
- **Single lightweight LLM** for task planning and control.
- Handles task sequences, skill control, and adjustments in **one context**.
- **No multiple agents, no cloud communication**.
- Low latency and high efficiency on edge devices like **Jetson Xavier Orin**.

## Installation

(你可以安装在linux pc，如果您需要在Jetson平台上运行，请确保您的Jetson设备已经安装了CUDA和cuDNN，并且已经安装了PyTorch。)
To install UniPlanner, follow these steps:

1. Clone the repository:
   ```
   git clone https://github.com/unira-zwj/uniplan.git
   ```

2. Install the required dependencies:
   ```
   pip install -r requirements.txt
   ```

## Before start
![Overview of UniPlanner](./images/Hardware_and_software.png "Magic Gardens")

**硬件连接**
- 如果您的机器人是UR + Robotiq（支持所有UR型号），您需要将UR机器人的网线与Jetson(或PC)连接
- 将Robotiq的USB线插入Jetson(或PC)。
- Inter D435相机的USB需要连接到Jetson(或PC)的USB3.0接口。
- 我们的代码中实现的是眼在手上的方式，所以需要将UR机械臂的末端执行器与相机对齐。并且下面的软件设置方式设置好您的机器人的坐标变换矩阵。
- 理论上代码是兼容眼在手外的安装方式，但您最好还是检查坐标变化是否正确

**软件设置**
- 您需要将UR机器人的IP地址设置为192.168.0.1，将Jetson(或PC)的IP地址设置为192.168.0.2（或者您也可以设置成别的，需要保证UR机械臂与主机的网段一致）
- 查询Robotiq的tty设备号（一般为'/dev/ttyUSB0'）
- 设置好UR机械臂的末端执行器与相机的坐标变换矩阵，您可以在uniplan.py中19行找到对应的设置
```python
R_C_to_T = np.eye(3)  # Rotation from camera to tool
t_C_to_T = np.array([-0.038, -0.065, -0.135])  # Translation from camera to tool
```
- 设置您机器人的Home起始点，这个位置是机械臂的初始位置，您必须尽量保证机械臂末端垂直工作台平面或者平行于工作台平面，您可以在uniplan.py中16行找到对应的设置
```python
HOME_POSE = [-0.025, -0.32, 0.2, 0, 3.133, 0] # 工作于垂直向下的任务（例如桌面上抓取）
HOME_POSE_H = [-0.025, -0.48, 0.15, 0, 2.24, -2.16] # 工作于水平操作的任务（例如开关抽屉）
```

**检查代码中的设置是否对应**
- uniplan.py中39行与40行，需要设置成您的UR机械臂的IP地址和Robotiq的tty设备号
```python
self.Robot = UR3("192.168.0.1")
self.Gripper = Robotiq85(MODBUS_PORT='/dev/ttyUSB0', BAUDRATE=115200)
```

**模型下载**
- 下载链接：🔗
- 您需要更改uniplanner_llm.py中第9行的模型路径，将其改为您下载的模型路径

## Quickstart

To use UniPlanner, follow these steps:

1. run the planner_llm:
   ```python
   $ python uniplanner_llm.py
   ```

2. run the planner:
   ```python
   $ python uniplan.py
   ```

## Other details
- 关于机器文章中提到的技能函数的定义在`./uniplanner/skill_functions.py`
- 关于机器人的技能实现在`./robot_skills/`目录下
- 关于机器人的基本api在`./robot_base_api/`目录下，理论上无论您是任何型号的机器人，只需要更改其中的api即可