import requests
import json

def test_delete_food(user_id, date, food_index):
    url = "http://localhost:5000/api/delete_food"
    headers = {'Content-Type': 'application/json'}
    data = {
        "ID": user_id,
        "DATE": date,
        "FOOD_INDEX": food_index
    }
    response = requests.delete(url, headers=headers, data=json.dumps(data))
    if response.status_code == 200:
        print("Success:", response.json())
    else:
        print("Error:", response.status_code, response.json())

if __name__ == '__main__':
    test_user_id = "상엽"
    test_date = "2024-08-05"
    test_food_index = 2  # 삭제할 음식의 인덱스

    test_delete_food(test_user_id, test_date, test_food_index)