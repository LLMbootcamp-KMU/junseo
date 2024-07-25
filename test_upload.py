import requests

# API 엔드포인트 URL
url = 'http://localhost:5000/api/upload'

# 파일 경로와 사용자 ID 설정
file_path = '/Users/junseo/Documents/langchain-kr/img/fri.jpeg'
user_id = '상엽'  # 테스트를 위한 사용자 ID

# 파일과 데이터 준비
files = {'file': open(file_path, 'rb')}
data = {'user_id': user_id}

# 요청 전송
response = requests.post(url, files=files, data=data)

# 응답 출력
print(response.json())