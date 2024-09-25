import os
import json
import time
from openai import OpenAI
import numpy as np
from transformers import pipeline

from uniplanner.robot_skills import (open_vocabulary_detect, pick_down, pick_horizon, put_down, 
                          open_horizon, close_horizon, wipe_down)
from uniplanner.robot_base_api import RealSenseD435Viewer, UR3, Robotiq85
from uniplanner.skill_functions import skill_functions
from uniplanner.utils import camera_to_tool


class UniPlanner:
    HOME_POSE = [-0.025, -0.32, 0.2, 0, 3.133, 0]
    HOME_POSE_H = [-0.025, -0.48, 0.15, 0, 2.24, -2.16]
    
    R_C_to_T = np.eye(3)  # Rotation from camera to tool
    t_C_to_T = np.array([-0.038, -0.065, -0.135])  # Translation from camera to tool

    system_prompt = [{
        "role": "system",
        "content": "You are an AI assistant and your task is to generate task planning and decision-making with function call sequences for the input robot task instructions."
    }]

    def __init__(self, go_home=True):
        self.client = OpenAI(
            api_key="0",
            base_url=f"http://localhost:{os.environ.get('API_PORT', 8000)}/v1"
        )
        
        print("\nPreloading detection model...")
        self.detector = pipeline(model="google/owlv2-base-patch16-ensemble", 
                                 task="zero-shot-object-detection", 
                                 device="cuda:0")

        print("\nInitializing robot and gripper...")
        self.Robot = UR3("192.168.0.1")
        self.Gripper = Robotiq85(MODBUS_PORT='/dev/ttyUSB0', BAUDRATE=115200)
        self.Gripper.open()

        if go_home:
            self.Robot.movel(self.HOME_POSE)

        print("\nInitializing RealSense camera...")
        self.viewer = RealSenseD435Viewer()
        self.viewer.start()

        self.llm_messages = self.system_prompt[:]

    def planner(self, task, horizon=False):
        print("\nReceived task input.\n")
        function_name = ""
        feedback = None

        task_goal, capabilities = self._parse_task(task)
        self.llm_messages.append({"role": "user", "content": task_goal})
        print("Task goal: " + task_goal)

        step, time_execute, time_llm = 1, 0, 0

        while function_name != "taskFinish":
            # LLM decision-making
            t1 = time.time()
            response = self._query_llm(capabilities)
            t2 = time.time()
            time_llm += t2 - t1
            print(response)
            self.llm_messages.append(response.choices[0].message)
            tool_calls = response.choices[0].message.tool_calls

            if tool_calls:
                function_name, parameters = self._extract_tool_call(tool_calls[0])
                print(f"\n\n**UniPlanner skill control {step}: \n{function_name}: {parameters}")

                # Perform action
                feedback = self._execute_action(function_name, parameters, horizon)
                self.llm_messages.append({"role": "tool", "content": feedback})
                print(f"\n==Execution feedback {step}: {feedback}")

                time_execute += time.time() - t1
                if function_name == 'taskFinish':
                    self._reset_llm()
                    print(f"LLM inference time: {time_llm}\nExecution time: {time_execute}\nCommunication time: 0")
                    return
                step += 1
            else:
                self._handle_llm_response(response, step)
    
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

        return task_goal, capabilities

    def _query_llm(self, capabilities):
        """Send the current conversation to the LLM and get a response."""
        return self.client.chat.completions.create(
            messages=self.llm_messages, 
            model="test", 
            tools=capabilities, 
            temperature=0.3
        )

    def _handle_llm_response(self, response, step):
        """Handle LLM response when no tool calls are present."""
        if 'Planning' in response.choices[0].message.content:
            user_input = "confirmed"
            print(f'\n\n**UniPlanner subtask plan:\n{response.choices[0].message.content}')
        else:
            user_input = "decision confirmed"
            print(f'\n\n**UniPlanner think {step}:\n{response.choices[0].message.content}')

        self.llm_messages.append({"role": "user", "content": user_input})

    def _extract_tool_call(self, tool_call):
        """Extract function name and parameters from LLM tool call."""
        function_name = tool_call.function.name
        parameters = json.loads(tool_call.function.arguments)
        return function_name, parameters

    def _execute_action(self, function_name, parameters, horizon):
        """Execute the corresponding robot action based on the function name."""
        target_uv = [320, 240]

        if "box" in parameters:
            target_uv[0] = int((parameters['box'][0] + parameters['box'][2]) / 2)
            target_uv[1] = int((parameters['box'][1] + parameters['box'][3]) / 2)

        color_image, depth_image, center_point, intrinsics = self.viewer.get_current_data(target_uv[0], target_uv[1])

        # Ensure valid depth point
        if function_name != "2dDetection":
            center_point = self._get_valid_depth_point(target_uv)

        tool_point = camera_to_tool(center_point, R_C_to_T=self.R_C_to_T, t_C_to_T=self.t_C_to_T)

        # Execute the corresponding skill function
        return self._execute_skill(function_name, tool_point, color_image, parameters, horizon)
    
    def _get_valid_depth_point(self, target_uv):
        """Ensure the depth point is within a valid range."""
        while True:
            _, _, center_point, _ = self.viewer.get_current_data(target_uv[0], target_uv[1])
            if 0.05 < center_point[2] < 0.6:
                return center_point

    def _execute_skill(self, function_name, tool_point, color_image, parameters, horizon):
        """Execute the specific skill based on the function name."""
        if function_name == "2dDetection":
            return open_vocabulary_detect(self.detector, color_image, parameters['object'], save_result=True)
        elif function_name == "pick":
            if horizon:
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

    def _reset_llm(self):
        """Reset the LLM conversation."""
        self.llm_messages = self.system_prompt[:]


if __name__ == "__main__":
    planner = UniPlanner()
    
    try:
        while True:
            # 2dDetection、pick、put<>put the blue block on the bowl.
            task = input("\n\ntask input: ")
            if task.lower() == "stop":
                break
            planner.planner(task, horizon=False)
    except KeyboardInterrupt:
        print("\nPlanner stopped by user.")
    finally:
        planner.viewer.stop()

