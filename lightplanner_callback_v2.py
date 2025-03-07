import os
import json
import time
import numpy as np
from transformers import pipeline
import base64
from io import BytesIO
from PIL import Image
import ast

from lightplanner.robot_skills import (open_vocabulary_detect, pick_down, pick_horizon, put_down, 
                          open_horizon, close_horizon, wipe_down)
from lightplanner.robot_base_api import RealSenseD435Viewer, UR3, Robotiq85
from lightplanner.skill_functions import skill_functions
from lightplanner.utils import camera_to_tool

import requests
import json

def llm_request(query, tools, url="http://localhost:8000/generate", timeout=60):
    payload = {
        "prompt": {
            "query": query,
            "tools": tools
        }
    }
    headers = {"Content-Type": "application/json"}
    try:
        response = requests.post(url, headers=headers, json=payload, timeout=timeout)
        response.raise_for_status()  # 如果响应状态码不是200，将引发HTTPError
        result = response.json()
        return result.get("response")
    except requests.exceptions.HTTPError as http_err:
        print(f"HTTP 错误：{http_err} - 响应内容：{response.text}")
    except requests.exceptions.ConnectionError as conn_err:
        print(f"连接错误：{conn_err}")
    except requests.exceptions.Timeout as timeout_err:
        print(f"请求超时：{timeout_err}")
    except requests.exceptions.RequestException as req_err:
        print(f"请求错误：{req_err}")
    except json.JSONDecodeError as json_err:
        print(f"JSON 解码错误：{json_err} - 响应内容：{response.text}")
    return None


def llm_request_streamed(query, tools, callback, url="http://localhost:8000/generate", timeout=60):
    """
    发送流式请求到LLM服务器，并通过callback实时传递生成的内容。

    :param query: 查询字符串
    :param tools: 工具字典
    :param callback: 接收每个生成数据块的回调函数
    :param url: LLM服务器的URL
    :param timeout: 请求超时时间
    :return: 完整的响应文本或None
    """
    payload = {
        "prompt": {
            "query": query,
            "tools": tools
        }
    }
    headers = {"Content-Type": "application/json"}
    response_text = ""
    
    try:
        with requests.post(url, headers=headers, json=payload, timeout=timeout, stream=True) as response:
            response.raise_for_status()
            # 假设服务器返回的是纯文本流
            for chunk in response.iter_content(chunk_size=1024, decode_unicode=True):
                if chunk:
                    response_text += chunk
                    if callback:
                        callback(chunk)  # 通过callback传递每个数据块
                    print(chunk, end='')  # 可选：实时打印
        return response_text.strip()
    except requests.exceptions.HTTPError as http_err:
        error_message = f"HTTP 错误：{http_err} - 响应内容：{response.text}"
        if callback:
            callback(error_message)
        print(error_message)
    except requests.exceptions.ConnectionError as conn_err:
        error_message = f"连接错误：{conn_err}"
        if callback:
            callback(error_message)
        print(error_message)
    except requests.exceptions.Timeout as timeout_err:
        error_message = f"请求超时：{timeout_err}"
        if callback:
            callback(error_message)
        print(error_message)
    except requests.exceptions.RequestException as req_err:
        error_message = f"请求错误：{req_err}"
        if callback:
            callback(error_message)
        print(error_message)
    except json.JSONDecodeError as json_err:
        error_message = f"JSON 解码错误：{json_err} - 响应内容：{response.text}"
        if callback:
            callback(error_message)
        print(error_message)
    return response_text if response_text else None


class UniPlanner:
    HOME_POSE = [-0.025, -0.32, 0.2, 0, 3.133, 0]
    HOME_POSE_H = [-0.025, -0.48, 0.15, 0, 2.24, -2.16]
    
    R_C_to_T = np.eye(3)  # Rotation from camera to tool
    t_C_to_T = np.array([-0.038, -0.07, -0.13])  # Translation from camera to tool
    

    def __init__(self, go_home=True):
        self.memories = ""
        
        print("\nPreloading detection model...")
        self.detector = pipeline(model="google/owlv2-base-patch16-ensemble", 
                                 task="zero-shot-object-detection", 
                                 device="cuda:0")

        print("\nInitializing robot and gripper...")
        self.Robot = UR3("192.168.0.1")
        self.Gripper = Robotiq85(MODBUS_PORT='/dev/ttyUSB0', BAUDRATE=115200)
        self.Gripper.open()

        if go_home:
            self.go_home()

        print("\nInitializing RealSense camera...")
        self.viewer = RealSenseD435Viewer()
        self.viewer.start()
        
    def memory_reset(self):
        self.memories = ""

    def planner(self, task, skills, horizon=False, callback=None, test=False):
        """
        Execute the task planning and execute corresponding actions.
        The callback function is called with output strings to update the UI.
        """
        self.Gripper.open()
        self.go_home(horizon=horizon)
        
        print("\nReceived task input.\n")
        function_name = ""
        feedback = None
        capabilities = [function for function in skill_functions if function['function']['name'] in skills]
        task_goal = self._parse_task(task)
        self.memories += "Got task goal.\n"
        
        step, time_execute, time_llm = 1, 0, 0
        while function_name != "taskFinish":
            if len(capabilities) == 0:
                print("must select skills!")
                callback("must select skills!")
                self.memory_reset()
                return
            
            t1 = time.time()
            query = f"Task goal: {task_goal}\nMemories: {self.memories}"
            # response = llm_request(query, capabilities)
            response = llm_request_streamed(query, capabilities, callback)
            llm_message = response
            # llm_message = response["response"]
            # callback(llm_message)
            
            t2 = time.time()
            time_llm += t2 - t1

            if "[action]" not in llm_message and "[/action]" not in llm_message:
                print("LLM respones do not have action decision.!!!")
                callback("\nLLM respones do not have action decision...return")
                self.memory_reset()
                return
            else:
                # 提取action
                try:
                    action_str = llm_message.split("[action]")[1].split("[/action]")[0].strip() # "{'name': '2dDetection', 'arguments': {'object': 'blue block'}}"
                    if action_str.startswith('"') and action_str.endswith('"'):
                        action_str = action_str[1:-1]
                    action_json = ast.literal_eval(action_str)
                    function_name = action_json['name']
                    parameters = action_json['arguments']
                except:
                    print(f"action extra error...: {action_str}")
                    callback("action extra error... check the llm respones")
                    self.memory_reset()
                    return
                
                # 机器人执行action
                try:
                    feedback = self._execute_action(function_name, parameters, horizon, test=test)
                    feedback_output = f"\n\n\n[Robot]Execution feedback {step}: \n{feedback}\n\n\n"
                    callback(feedback_output)
                    self.memories += f"[action]{function_name}({parameters})[/action]\n[results]{feedback}[/results]\n\n"
                except Exception as e:
                    print(f"skill executed error...{e}")
                    callback("Skill executed error... finish")
                    self.memory_reset()
                    return
                
                if function_name == 'taskFinish':
                    final_output = f"LLM inference time: {time_llm}\nExecution time: {time_execute}\nCommunication time: 0\n"
                    # callback(final_output)
                    print(final_output)
                    self.memory_reset()
                    return final_output
                
                # 回传检测结果图片
                if function_name == "2dDetection" and callback and not test:
                    img = Image.open("./save_images/detect_result.jpg").convert("RGB")
                    callback(img)
                    print("send detect result...")

                time_execute += time.time() - t1
                step += 1 

    def go_home(self, horizon=False):
        if horizon:
            self.Robot.movel(self.HOME_POSE_H, acc=0.3)
        else:
            self.Robot.movel(self.HOME_POSE, acc=0.3)
    
    def _parse_task(self, task):
        """Parse the task input and extract task goal and capabilities."""
        if task is None:
            task = input("Task goal: ")
        if "<>" in task:
            skills, task_goal = task.split("<>")
            capabilities = [func for func in skill_functions if func['function']['name'] in skills.split("、")]
        else:
            task_goal = task
            capabilities = skill_functions
        return task_goal

    def _execute_action(self, function_name, parameters, horizon, test=False):
        """Execute the corresponding robot action based on the function name."""
        target_uv = [320, 240]

        if "box" in parameters:
            target_uv[0] = int((parameters['box'][0] + parameters['box'][2]) / 2)
            target_uv[1] = int((parameters['box'][1] + parameters['box'][3]) / 2)

        color_image, depth_image, center_point, intrinsics = self.viewer.get_current_data(target_uv[0], target_uv[1])
        
        if test:
            return self._execute_skill(function_name, (1,1,1), color_image, parameters, horizon ,test=test)
        
        # Ensure valid depth point
        if function_name != "2dDetection":
            center_point = self._get_valid_depth_point(target_uv)
        if center_point is None:
            return None
        
        tool_point = camera_to_tool(center_point, R_C_to_T=self.R_C_to_T, t_C_to_T=self.t_C_to_T)

        # Execute the corresponding skill function
        return self._execute_skill(function_name, tool_point, color_image, parameters, horizon ,test=test)
    
    def _get_valid_depth_point(self, target_uv):
        """Ensure the depth point is within a valid range."""
        n = 0
        while n < 10:
            _, _, center_point, _ = self.viewer.get_current_data(target_uv[0], target_uv[1])
            if 0.05 < center_point[2] < 0.6:
                return center_point
            else:
                print("center point's depth {} out of range.".format(center_point[2]))
                time.sleep(0.5)
                n += 1
        return None

    def _execute_skill(self, function_name, tool_point, color_image, parameters, horizon, test=False):
        if test:
            if function_name == "2dDetection":
                return "xmin: 123, ymin: 123, xmax:234, ymax: 234"
            else:
                return "successful"
        """Execute the specific skill based on the function name."""
        if function_name == "2dDetection":
            return open_vocabulary_detect(self.detector, color_image, parameters['object'], save_result=True)
        elif function_name == "pick":
            print("pick")
            if horizon:
                print("pick horizon")
                return pick_horizon(tool_point, self.HOME_POSE_H, Arm=self.Robot, Gripper=self.Gripper, put_down=True, HOME_POSE_D=self.HOME_POSE)
            return pick_down(tool_point, self.HOME_POSE, Arm=self.Robot, Gripper=self.Gripper)
        elif function_name == "put":
            return put_down(tool_point, self.HOME_POSE, Arm=self.Robot, Gripper=self.Gripper)
        elif function_name == "open":
            return open_horizon(tool_point, self.HOME_POSE_H, Arm=self.Robot, Gripper=self.Gripper)
        elif function_name == "close":
            return close_horizon(tool_point, self.HOME_POSE_H, Arm=self.Robot, Gripper=self.Gripper)
        elif function_name == "wipe":
            return wipe_down(tool_point, self.HOME_POSE, Arm=self.Robot, Gripper=self.Gripper)
        elif function_name == "taskFinish":
            return None
        else:
            return None
