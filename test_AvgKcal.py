import requests
import json

def test_get_avg_kcal():
    url = "http://localhost:5001/api/food/avg_kcal"
    params = {
        "year": 2024,
        "month": 2,
        "user_id": "상엽"  # 테스트할 사용자 ID
    }

    response = requests.get(url, params=params)

    if response.status_code == 200:
        data = response.json()
        print(json.dumps(data, indent=4, ensure_ascii=False))
        # 추가 검증 로직을 여기에 작성할 수 있습니다.
        # 예: assert data["average_kcal"] > 0, "평균 칼로리가 0보다 커야 합니다."
    else:
        print("Error:", response.status_code, response.text)

if __name__ == '__main__':
    test_get_avg_kcal()