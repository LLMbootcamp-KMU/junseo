import requests
import json

def test_get_day_food():
    url = "http://localhost:5001/api/food/get_day"
    params = {
        "year": 2024,
        "month": 3,
        "day": 24,
        "user_id": "상엽"  # 테스트할 사용자 ID
    }

    response = requests.get(url, params=params)

    if response.status_code == 200:
        data = response.json()
        print(json.dumps(data, indent=4, ensure_ascii=False))
    else:
        print("Error:", response.status_code, response.text)

if __name__ == '__main__':
    test_get_day_food()