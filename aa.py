from langchain_openai import AzureChatOpenAI
from langchain.schema import HumanMessage, SystemMessage
from dotenv import load_dotenv
import os
import base64
import json

# 환경 변수 로드
load_dotenv()

# Azure OpenAI 클라이언트 설정
client = AzureChatOpenAI(
    openai_api_key=os.getenv("AZURE_OPENAI_API_KEY"),
    openai_api_version=os.getenv("OPENAI_API_VERSION"),
    azure_endpoint=os.getenv("AZURE_OPENAI_ENDPOINT"),
    deployment_name=os.getenv("AZURE_OPENAI_DEPLOYMENT")
)

def encode_image(image_path):
    if not os.path.exists(image_path):
        raise FileNotFoundError(f"이미지 파일이 존재하지 않습니다: {image_path}")
    
    with open(image_path, "rb") as image_file:
        return base64.b64encode(image_file.read()).decode('utf-8')

def extract_info_from_image(image_path, prompt):
    base64_image = encode_image(image_path)

    # 메시지 구성
    messages = [
        SystemMessage(content=prompt),
        HumanMessage(content=json.dumps([
            {
                "type": "image_url",
                "image_url": {
                    "url": f"data:image/jpeg;base64,{base64_image}"
                }
            },
            {
                "type": "text",
                "text": "이 음식 이미지에서 음식 이름을 알려주세요."
            }
        ]))
    ]

    response = client.invoke(messages)
    return response.content

# 프롬프트 템플릿
prompt = """
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

# 이미지 파일 경로 설정
image_path = "hamburger.jpeg"  # 업로드한 이미지 파일 경로


response = extract_info_from_image(image_path, prompt)
print(response)