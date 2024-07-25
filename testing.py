import base64
from io import BytesIO
from PIL import Image
import os
from dotenv import load_dotenv
import json

load_dotenv()

def convert_to_base64(image_path):
    with Image.open(image_path) as image:
        buffered = BytesIO()
        image.save(buffered, format="JPEG")
        img_str = base64.b64encode(buffered.getvalue()).decode("utf-8")
    return img_str

image_base64 = convert_to_base64("/Users/junseo/Documents/langchain-kr/salad.jpeg")

from langchain_core.messages import HumanMessage
from langchain_openai import AzureChatOpenAI

def create_prompt(image_base64, text_prompt):
    message = HumanMessage(
        content=[
            {"type": "text", "text": text_prompt},
            {
                "type": "image_url", 
                "image_url": {
                    "url": f"data:image/jpeg;base64,{image_base64}"
                }
            },
        ]
    )
    return [message]

text_prompt = """
당신은 음식 이미지에서 음식이름을 추출하는 최고의 전문가입니다. 주어진 음식 이미지를 세심하게 분석하여 다음 정보를 정확하게 추출해주세요. 추출한 정보는 반드시 아래 지정된 JSON 형식으로 반환해야 합니다.

추출할 정보:
- 음식이름: 한글로 음식 이름

주의사항:
1. 정보가 없는 경우 해당 필드를 공백 한 칸 문자열(" ")로 설정하세요.
2. JSON 형식을 엄격히 준수하세요.

반환 형식:
{
"음식": "음식 이름"
}
"""

message = create_prompt(image_base64, text_prompt)

def invoke_model(message):
    model = AzureChatOpenAI(
        openai_api_key=os.getenv("AZURE_OPENAI_API_KEY"),
        openai_api_version=os.getenv("OPENAI_API_VERSION"),
        azure_endpoint=os.getenv("AZURE_OPENAI_ENDPOINT"),
        deployment_name=os.getenv("AZURE_OPENAI_DEPLOYMENT")
    )
    result = model.invoke(message)
    return result

response = invoke_model(message)

# 응답을 JSON 형식으로 변환
def parse_response_to_json(response):
    try:
        response_text = response.content
        response_json = json.loads(response_text)
        return response_json
    except Exception as e:
        return {"error": str(e)}

response_json = parse_response_to_json(response)
print(json.dumps(response_json, ensure_ascii=False, indent=4))