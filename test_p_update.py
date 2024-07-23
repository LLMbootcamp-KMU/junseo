# test_profile_update.py

import requests
import json

def test_update_profile():
    url = "http://localhost:5000/api/p_update"  # Flask 서버의 엔드포인트 URL

    # 업데이트할 사용자 정보 (예시)
    data = {
        "id": "상엽",  # 기존 사용자 ID
        "BODY_WEIGHT": 100,  # 변경할 값
        "HEIGHT": 100,     # 변경할 값
        "AGE": 100,         # 변경할 값
        "ACTIVITY": 4      # 변경할 값
    }

    headers = {
        "Content-Type": "application/json"
    }

    print(f"Sending request to {url} with data: {data}")
    response = requests.post(url, headers=headers, data=json.dumps(data))

    # 응답 확인
    print(f"Response status code: {response.status_code}")
    if response.status_code == 200:
        print("Profile updated successfully.")
        print("Response:", response.json())
    else:
        print("Failed to update profile.")
        print("Status Code:", response.status_code)
        print("Response:", response.json())

if __name__ == "__main__":
    test_update_profile()