import requests
import json

def test_update_food(user_id, date, food_index, new_food_name):
    url = "http://localhost:5000/api/update_food"
    headers = {'Content-Type': 'application/json'}
    data = {
        "ID": user_id,
        "DATE": date,
        "FOOD_INDEX": food_index,
        "NEW_FOOD_NAME": new_food_name
    }
    response = requests.post(url, headers=headers, data=json.dumps(data))
    
    try:
        response_json = response.json()
    except requests.exceptions.JSONDecodeError:
        response_json = None
    
    if response.status_code == 200:
        print("Update Success:", response_json)
    else:
        print("Update Error:", response.status_code, response_json)

if __name__ == '__main__':
    test_user_id = "상엽"
    test_date = "2024-07-01"
    test_food_index = 8  # 수정할 FOOD_INDEX 값을 설정합니다.
    new_food_name = "라면"
    
    # 음식 수정 테스트
    print("Updating Food...")
    test_update_food(test_user_id, test_date, test_food_index, new_food_name)