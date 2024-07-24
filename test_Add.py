import requests
import json

def test_add_food(user_id, date, food_name):
    url = "http://localhost:5000/api/add_food"
    headers = {'Content-Type': 'application/json'}
    data = {
        "ID": user_id,
        "DATE": date,
        "FOOD_NAME": food_name
    }
    response = requests.post(url, headers=headers, data=json.dumps(data))
    
    try:
        response_json = response.json()
    except requests.exceptions.JSONDecodeError:
        response_json = None
    
    if response.status_code == 201:
        print("Success:", response_json)
    else:
        print("Error:", response.status_code, response_json)

if __name__ == '__main__':
    test_user_id = "상엽"
    test_date = "2024-07-01"
    test_food_name = "햄버거"
    
    # 음식 추가 테스트
    test_add_food(test_user_id, test_date, test_food_name)