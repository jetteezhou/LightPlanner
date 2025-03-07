
from fastapi import FastAPI, HTTPException
from fastapi.responses import StreamingResponse
from pydantic import BaseModel
from transformers import AutoModelForCausalLM, AutoTokenizer
import torch
import asyncio

app = FastAPI(
    title="UniPlanner-v2",
    description="UniPlanner-v2 LLM Streamed Serve",
    version="2.0"
)

# 定义请求体的结构
class GenerateRequest(BaseModel):
    prompt: dict

# 定义响应体的结构
class GenerateResponse(BaseModel):
    response: dict

# 载入模型和分词器
model_name = "checkpoints"
device = "cuda" if torch.cuda.is_available() else "cpu"


try:
    model = AutoModelForCausalLM.from_pretrained(
        model_name,
        torch_dtype=torch.float16 if device == "cuda" else torch.float32,
        device_map="auto" if device == "cuda" else None,
    )
    tokenizer = AutoTokenizer.from_pretrained(model_name)
    model.eval()  # 将模型设置为评估模式
except Exception as e:
    print(f"模型加载失败: {e}")
    raise e

async def generate_stream(prompt: str, tools: dict):
    messages = [
        {"role": "system", "content": "..."},
        {"role": "user", "content": prompt}
    ]

    try:
        text = tokenizer.apply_chat_template(messages, tools=tools, tokenize=False, add_generation_prompt=True)
        input_ids = tokenizer.encode(text, return_tensors="pt").to(device)
        
        # 初始化关键参数
        past_key_values = None
        generated_ids = input_ids.clone()
        current_token = input_ids

        with torch.no_grad():
            for _ in range(512):
                # 每次传入当前token和缓存
                outputs = model(
                    input_ids=current_token,
                    past_key_values=past_key_values,
                    use_cache=True  # 启用缓存机制
                )
                
                # 更新缓存
                past_key_values = outputs.past_key_values
                
                # 获取下一个token
                next_token = torch.argmax(outputs.logits[:, -1, :], dim=-1)
                
                # 拼接生成结果
                generated_ids = torch.cat([generated_ids, next_token.unsqueeze(-1)], dim=-1)
                
                # 下次迭代只需传入当前token
                current_token = next_token.unsqueeze(-1)
                
                # 解码并返回
                decoded_token = tokenizer.decode(current_token[0], skip_special_tokens=False)
                                
                if '<|im_end|>' in decoded_token:
                    break
                
                yield decoded_token
                await asyncio.sleep(0)

    except Exception as e:
        yield f"Error: {str(e)}"
    finally:
        # 显式释放资源
        del past_key_values, outputs, current_token
        torch.cuda.empty_cache()

@app.post("/generate", response_model=None)
async def generate_text(request: GenerateRequest):
    prompt = request.prompt.get("query")
    tools = request.prompt.get("tools")

    if not prompt:
        raise HTTPException(status_code=400, detail="缺少 'query' 字段")

    return StreamingResponse(
        generate_stream(prompt, tools),
        media_type="text/plain"
    )

@app.get("/", response_model=GenerateResponse)
def read_root():
    return GenerateResponse(response="UniPlanner")
