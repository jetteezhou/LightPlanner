from fastapi import FastAPI, Request
from transformers import AutoModelForCausalLM, AutoTokenizer
import torch
from pydantic import BaseModel

app = FastAPI()

# 配置模型路径和设备
model_name = "/home/chan/zhouweijie/qwen2/checkpoint2-qwen2-1.5B"
device = "cuda"

# 加载模型和 tokenizer
model = AutoModelForCausalLM.from_pretrained(
    model_name,
    torch_dtype="auto",
    device_map=device,
)
tokenizer = AutoTokenizer.from_pretrained(model_name)

# 请求体模型
class ChatRequest(BaseModel):
    model: str
    messages: list
    max_tokens: int = 512

# 生成响应的函数
def generate_response_local(messages, max_tokens=512):
    # 将消息模板化并进行tokenize
    text = tokenizer.apply_chat_template(
        messages,
        tokenize=False,
        add_generation_prompt=True
    )
    model_inputs = tokenizer([text], return_tensors="pt").to(device)
    
    # 生成响应
    generated_ids = model.generate(
        **model_inputs,
        max_new_tokens=max_tokens
    )
    
    # 只取生成的新token部分
    generated_ids = [
        output_ids[len(input_ids):] for input_ids, output_ids in zip(model_inputs.input_ids, generated_ids)
    ]
    
    # 解码生成的tokens
    response = tokenizer.batch_decode(generated_ids, skip_special_tokens=True)[0]
    print(response)
    return response

# 定义 API 路由
@app.post("/v1/chat/completions")
async def chat_completions(request: ChatRequest):
    try:
        # prompt = request.messages[-1]["content"]
        # max_tokens = request.max_tokens
        max_tokens = 512
        
        # 生成响应
        response_text = generate_response_local(request, max_tokens)
        
        # 构造返回的JSON格式，模仿OpenAI API
        response = {
            "id": "chatcmpl-123456789",
            "object": "chat.completion",
            "created": int(torch.time.time()),
            "model": model_name,
            "choices": [
                {
                    "index": 0,
                    "message": {
                        "role": "assistant",
                        "content": response_text
                    },
                    "finish_reason": "stop"
                }
            ],
            "usage": {
                "prompt_tokens": len(tokenizer.encode(request)),
                "completion_tokens": len(tokenizer.encode(response_text)),
                "total_tokens": len(tokenizer.encode(request)) + len(tokenizer.encode(response_text))
            }
        }
        return response
    
    except Exception as e:
        return {"error": str(e)}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
