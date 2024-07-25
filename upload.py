from flask import Flask, request, jsonify
import pymysql
import os
from dotenv import load_dotenv
from datetime import datetime
import upload_llm as llm

load_dotenv()

app = Flask(__name__)

# DB Connection
db_config = {
    'host': os.getenv('DB_HOST'),
    'user': os.getenv('DB_USER'),
    'password': os.getenv('DB_PASSWORD'),
    'database': os.getenv('DB_NAME')
}

def save_to_db(user_id, nutrition_info):
    connection = pymysql.connect(**db_config)
    try:
        with connection.cursor() as cursor:
            sql = """
                INSERT INTO FOOD (ID, DATE, FOOD_NAME, FOOD_PT, FOOD_FAT, FOOD_CH, FOOD_KCAL)
                VALUES (%s, %s, %s, %s, %s, %s, %s)
            """
            cursor.execute(sql, (
                user_id,
                datetime.now(),  # 현재 날짜와 시간 저장
                nutrition_info['food_name'],
                nutrition_info['protein'],
                nutrition_info['fat'],
                nutrition_info['carbohydrate'],
                nutrition_info['calorie']
            ))
            print("Data saved to database")  # Debugging 출력 추가
        connection.commit()
    finally:
        connection.close()

@app.route('/api/upload', methods=['POST'])
def upload():
    user_id = request.form.get('user_id')
    if 'file' not in request.files:
        return jsonify({"error": "No file part"}), 400

    file = request.files['file']
    if file.filename == '':
        return jsonify({"error": "No selected file"}), 400

    if file:
        file_path = os.path.join("/tmp", file.filename)
        file.save(file_path)

        nutrition_info = llm.do(file_path)
        
        if 'error' in nutrition_info:
            return jsonify(nutrition_info), 400
        
        save_to_db(user_id, nutrition_info)
        
        return jsonify(nutrition_info)

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)