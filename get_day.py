from flask import Flask, request, jsonify
import pymysql
import os
from dotenv import load_dotenv
import logging

load_dotenv()

app = Flask(__name__)

# DB Connection
db_config = {
    'host': os.getenv('DB_HOST'),
    'user': os.getenv('DB_USER'),
    'password': os.getenv('DB_PASSWORD'),
    'database': os.getenv('DB_NAME')
}

# Logger 설정
logging.basicConfig(level=logging.DEBUG)

def get_user_nutritional_needs(user_id):
    connection = pymysql.connect(**db_config)
    try:
        with connection.cursor() as cursor:
            sql = "SELECT BODY_WEIGHT, RDI FROM USER WHERE ID = %s"
            cursor.execute(sql, (user_id,))
            result = cursor.fetchone()
            if result:
                body_weight, rdi = result
                return body_weight, rdi
            else:
                return None
    except pymysql.MySQLError as e:
        logging.error(f"Database error: {e}")
        return None
    finally:
        connection.close()

def get_daily_totals(user_id, date):
    connection = pymysql.connect(**db_config)
    try:
        with connection.cursor() as cursor:
            sql = "SELECT CARBO, PROTEIN, FAT, RD_CARBO, RD_PROTEIN, RD_FAT FROM USER_NT WHERE ID = %s AND DATE = %s"
            cursor.execute(sql, (user_id, date))
            result = cursor.fetchone()
            if result:
                return result
            else:
                return None
    except pymysql.MySQLError as e:
        logging.error(f"Database error: {e}")
        return None
    finally:
        connection.close()

def get_foods_by_date(year, month, day, user_id):
    connection = pymysql.connect(**db_config)
    try:
        with connection.cursor() as cursor:
            sql = """
                SELECT DATE, FOOD_INDEX, FOOD_NAME, FOOD_PT, FOOD_FAT, FOOD_CH, FOOD_KCAL
                FROM FOOD
                WHERE YEAR(DATE) = %s AND MONTH(DATE) = %s AND DAY(DATE) = %s AND ID = %s
                ORDER BY DATE
            """
            cursor.execute(sql, (year, month, day, user_id))
            results = cursor.fetchall()
            foods_list = []  # 특정 날짜의 음식 리스트
            percentages = {"carbohydrates_percentage": 0, "protein_percentage": 0, "fat_percentage": 0}  # 기본값 0으로 설정

            for row in results:
                food_info = {
                    "food_index": row[1],
                    "food_name": row[2],
                    "protein": row[3],
                    "fat": row[4],
                    "carbohydrates": row[5],
                    "calories": row[6]
                }
                foods_list.append(food_info)

            # Add daily percentages
            date_str = f"{year}-{str(month).zfill(2)}-{str(day).zfill(2)}"  # 날짜 문자열
            daily_totals = get_daily_totals(user_id, date_str)
            if daily_totals:
                carb_total, protein_total, fat_total, rd_carb, rd_protein, rd_fat = daily_totals
                percentages = {
                    "carbohydrates_percentage": round((carb_total / rd_carb) * 100, 1) if rd_carb > 0 else 0,
                    "protein_percentage": round((protein_total / rd_protein) * 100, 1) if rd_protein > 0 else 0,
                    "fat_percentage": round((fat_total / rd_fat) * 100, 1) if rd_fat > 0 else 0
                }

            return {
                "foods": foods_list,
                "percentages": percentages
            }
    except pymysql.MySQLError as e:
        logging.error(f"Database error: {e}")
        return {"error": "Database error"}
    finally:
        connection.close()

@app.route('/api/food/get_day', methods=['GET'])
def get_day_food():
    year = request.args.get('year')
    month = request.args.get('month')
    day = request.args.get('day')
    user_id = request.args.get('user_id')

    if not year or not month or not day or not user_id:
        return jsonify({"error": "Year, month, day, and user_id are required"}), 400

    try:
        year = int(year)
        month = int(month)
        day = int(day)
        if month < 1 or month > 12 or day < 1 or day > 31:
            return jsonify({"error": "Invalid month or day. Please enter valid values."}), 400
    except ValueError:
        return jsonify({"error": "Year, month, and day must be integers."}), 400

    daily_data = get_foods_by_date(year, month, day, user_id)

    if "error" in daily_data:
        logging.error(f"Failed to get daily data: {daily_data['error']}")
        return jsonify(daily_data), 500

    return jsonify(daily_data)

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5001)  # 다른 포트로 실행하여 send.py와 충돌 방지