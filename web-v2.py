import gradio as gr
import threading
import queue
from PIL import Image
import time
import numpy as np
import re

from lightplanner_callback_v2 import UniPlanner
from lightplanner.skill_functions import skill_functions

import logging
logging.getLogger("gradio").setLevel(logging.WARNING)

# 获取可用的技能函数名称
SKILL_FUNCTIONS_AVAILABLE = [func['function']['name'] for func in skill_functions]

# 初始化 UniPlanner 实例
planner = UniPlanner()

def run_planner(task, selected_skills, horizon_selection, test):
    """
    运行 UniPlanner 的 planner 方法，并实时通过生成器传输累积输出和图像。
    图像以 PIL Image 对象形式传输。
    """
    # 在开始时清空输出和图像展示
    yield ("", [])
    
    q = queue.Queue()
    accumulated_output = ""
    images = []
    
    # 根据用户选择设置 horizon 参数
    horizon = True if horizon_selection == "水平" else False
    
    test_ = True if test == 'true' else False

    def callback(message):
        q.put(message)

    def execute_planner():
        try:
            planner.planner(task=task, horizon=horizon, skills=selected_skills, callback=callback, test=test_)
        except Exception as e:
            q.put(f"Error: {str(e)}")
        finally:
            q.put(None)  # 使用 None 作为完成的信号

    # 启动后台线程执行规划
    thread = threading.Thread(target=execute_planner)
    thread.start()

    while True:
        msg = q.get()
        if msg is None:
            break
        if isinstance(msg, Image.Image):
            images.append(msg)
            if len(images) > 4:
                images.pop(0)
        else:
            accumulated_output += msg  # 累积输出
            
            pattern = re.compile(r'<think>(.*?)<\/think>\s*(.*?)(?=<think>|$)', re.DOTALL)
            matches = pattern.findall(accumulated_output)
            
            formatted_output = ""
            processed_length = 0  # 记录处理的字符长度，以便后续处理未闭合的 <think>
            
            for think, summary in matches:
                # 格式化思考内容
                think_formatted = think.strip().replace('\n', '\n >\n> ')
                # 格式化总结内容
                summary_formatted = summary.strip()
                
                # 拼接格式化后的内容
                formatted_output += "\n\n> **深度思考**\n> \n> {}\n\n {}".format(think_formatted, summary_formatted)
                
                # 更新已处理的长度
                # 计算当前匹配的位置
                match_str = f"<think>{think}</think>{summary}"
                processed_length += len(match_str)
            
            # 检查是否存在未闭合的 <think> 标签
            remaining_output = accumulated_output[processed_length:]
            open_think_match = re.search(r'<think>(.*)', remaining_output, re.DOTALL)
            
            if open_think_match:
                # 提取未闭合的思考内容
                think_content = open_think_match.group(1).strip().replace('\n', '\n >\n> ')
                # 格式化未闭合的思考内容
                formatted_output += "\n\n> **深度思考**\n> \n> {}".format(think_content)
            
            # 生成最终的格式化输出和图像列表的副本
            yield (formatted_output, images.copy())

with gr.Blocks() as demo:
    gr.Markdown("# UniPlanner-R1 ")
    
    with gr.Row():
        skill_selection = gr.CheckboxGroup(
            choices=SKILL_FUNCTIONS_AVAILABLE,
            label="选择技能",
            info="请选择要启用的技能",
            value=[]  # 默认空选择
        )
    
    with gr.Row():
        horizon_select = gr.Radio(
            choices=["水平", "向下"],
            label="机械臂home位置",
            info="请选择机械臂的home位置方向",
            value="向下"  # 默认选择“向下”
        )
        
    with gr.Row():
        test = gr.Radio(
            choices=["true", "false"],
            label="测试",
            info="",
            value="true"  # 默认选择“true”
        )
        
    with gr.Row():
        task_input = gr.Textbox(
            lines=2,
            placeholder="输入您的任务，例如：Pick the red block and place it on the table.",
            label="任务输入"
        )
    
    run_button = gr.Button("运行任务规划")
    
    # 输出文本框 (使用 Markdown 以支持格式化)
    output_box = gr.Markdown(
        value="",               # 初始内容为空
        label="大模型输出（深度推理think + 行动决策）",
    )
    
    # 添加图像展示组件（使用 Gallery 可显示多张图片）
    image_gallery = gr.Gallery(
        label="感知结果可视化",
        columns=4,    # 设置每行显示的图片数量
        height="auto"
    )
    
    # 配置点击事件，启用 streaming
    run_button.click(
        run_planner, 
        inputs=[task_input, skill_selection, horizon_select, test], 
        outputs=[output_box, image_gallery],
        show_progress=False  # Gradio 将处理流式更新
    )

# 运行 Gradio 应用
if __name__ == "__main__":
    demo.launch()
