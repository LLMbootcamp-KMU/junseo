from flask import Flask, request, jsonify
import pymysql
import os
from dotenv import load_dotenv
from llm import do as llm_do  # llm.py 파일에서 do 함수를 import

# 환경 변수 로드
print("Loading .env file...")
load_dotenv()

app = Flask(__name__)

# DB Connection
db_config = {
    'host': os.getenv('DB_HOST'),
    'user': os.getenv('DB_USER'),
    'password': os.getenv('DB_PASSWORD'),
    'database': os.getenv('DB_NAME')
}

@app.route('/api/add_food', methods=['POST'])
def add_food():
    data = request.json
    
    user_id = data.get('ID')
    date = data.get('DATE')
    food_name = data.get('FOOD_NAME')
    
    if not user_id or not date or not food_name:
        return jsonify({"error": "필수 정보가 누락되었습니다."}), 400

    # LLM을 통해 음식 영양 정보를 가져옴
    nutrition_info = llm_do(food_name)

    try:
        connection = pymysql.connect(**db_config)
        with connection.cursor() as cursor:
            # FOOD_INDEX를 구함 (해당 날짜의 가장 높은 인덱스를 찾아 +1)
            cursor.execute("SELECT MAX(FOOD_INDEX) FROM FOOD WHERE ID = %s AND DATE = %s", (user_id, date))
            max_index = cursor.fetchone()[0]
            food_index = max_index + 1 if max_index is not None else 0

            insert_query = """
            INSERT INTO FOOD (ID, DATE, FOOD_INDEX, FOOD_NAME, FOOD_CH, FOOD_PT, FOOD_FAT, FOOD_KCAL)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
            """
            cursor.execute(insert_query, (
                user_id, date, food_index,
                nutrition_info['food_name'],
                nutrition_info['carbohydrate'],
                nutrition_info['protein'],
                nutrition_info['fat'],
                nutrition_info['calorie']
            ))
            connection.commit()

            added_food_info = {
                "ID": user_id,
                "DATE": date,
                "FOOD_INDEX": food_index,
                "FOOD_NAME": nutrition_info['food_name'],
                "FOOD_CH": nutrition_info['carbohydrate'],
                "FOOD_PT": nutrition_info['protein'],
                "FOOD_FAT": nutrition_info['fat'],
                "FOOD_KCAL": nutrition_info['calorie']
            }

            return jsonify({"message": "음식이 성공적으로 추가되었습니다.", "data": added_food_info}), 201

    except pymysql.MySQLError as e:
        return jsonify({"error": str(e)}), 500

    finally:
        connection.close()

@app.route('/api/update_food', methods=['POST'])
def update_food():
    data = request.json

    user_id = data.get('ID')
    date = data.get('DATE')
    food_index = data.get('FOOD_INDEX')
    new_food_name = data.get('NEW_FOOD_NAME')
    
    if not user_id or not date or not food_index or not new_food_name:
        return jsonify({"error": "필수 정보가 누락되었습니다."}), 400

    # LLM을 통해 새로운 음식 영양 정보를 가져옴
    new_nutrition_info = llm_do(new_food_name)

    try:
        connection = pymysql.connect(**db_config)
        with connection.cursor() as cursor:
            update_query = """
            UPDATE FOOD
            SET FOOD_NAME = %s, FOOD_CH = %s, FOOD_PT = %s, FOOD_FAT = %s, FOOD_KCAL = %s
            WHERE ID = %s AND DATE = %s AND FOOD_INDEX = %s
            """
            cursor.execute(update_query, (
                new_nutrition_info['food_name'],
                new_nutrition_info['carbohydrate'],
                new_nutrition_info['protein'],
                new_nutrition_info['fat'],
                new_nutrition_info['calorie'],
                user_id, date, food_index
            ))
            connection.commit()

            updated_food_info = {
                "ID": user_id,
                "DATE": date,
                "FOOD_INDEX": food_index,
                "FOOD_NAME": new_nutrition_info['food_name'],
                "FOOD_CH": new_nutrition_info['carbohydrate'],
                "FOOD_PT": new_nutrition_info['protein'],
                "FOOD_FAT": new_nutrition_info['fat'],
                "FOOD_KCAL": new_nutrition_info['calorie']
            }

            return jsonify({"message": "음식이 성공적으로 수정되었습니다.", "data": updated_food_info}), 200

    except pymysql.MySQLError as e:
        return jsonify({"error": str(e)}), 500

    finally:
        connection.close()

if __name__ == '__main__':
    app.run(debug=True)