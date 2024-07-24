from flask import Flask, request, jsonify
import pymysql
import os
from dotenv import load_dotenv
import logging
import calendar

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

def get_monthly_data(year, month, user_id):
    connection = pymysql.connect(**db_config)
    try:
        with connection.cursor() as cursor:
            sql = """
                SELECT DATE, FOOD_INDEX, FOOD_NAME, FOOD_PT, FOOD_FAT, FOOD_CH, FOOD_KCAL
                FROM FOOD
                WHERE YEAR(DATE) = %s AND MONTH(DATE) = %s AND ID = %s
                ORDER BY DATE
            """
            cursor.execute(sql, (year, month, user_id))
            results = cursor.fetchall()

            num_days = calendar.monthrange(year, month)[1]  # 해당 월의 일수 계산
            foods_list = [[] for _ in range(num_days)]  # 각 날짜별 음식 리스트
            percentages_list = [{} for _ in range(num_days)]  # 각 날짜별 백분율 리스트

            for row in results:
                day = row[0].day - 1  # 0-based index for lists
                food_info = {
                    "food_index": row[1],
                    "food_name": row[2],
                    "protein": row[3],
                    "fat": row[4],
                    "carbohydrates": row[5],
                    "calories": row[6]
                }
                foods_list[day].append(food_info)

            # Add daily percentages
            for day in range(num_days):
                date_str = f"{year}-{str(month).zfill(2)}-{str(day+1).zfill(2)}"  # 1-based day for dates
                daily_totals = get_daily_totals(user_id, date_str)
                if daily_totals:
                    carb_total, protein_total, fat_total, rd_carb, rd_protein, rd_fat = daily_totals
                    percentages_list[day] = {
                        "carbohydrates_percentage": round((carb_total / rd_carb) * 100, 1) if rd_carb > 0 else 0,
                        "protein_percentage": round((protein_total / rd_protein) * 100, 1) if rd_protein > 0 else 0,
                        "fat_percentage": round((fat_total / rd_fat) * 100, 1) if rd_fat > 0 else 0
                    }

            return {
                "foods": foods_list,
                "percentages": percentages_list
            }
    except pymysql.MySQLError as e:
        logging.error(f"Database error: {e}")
        return {"error": "Database error"}
    finally:
        connection.close()

@app.route('/api/food/quarterly', methods=['GET'])
def get_quarterly_food():
    year = request.args.get('year')
    start_month = request.args.get('month')
    user_id = request.args.get('user_id')

    if not year or not start_month or not user_id:
        return jsonify({"error": "Year, start month, and user_id are required"}), 400

    try:
        year = int(year)
        start_month = int(start_month)
        if start_month < 1 or start_month > 12:
            return jsonify({"error": "Invalid month. Please enter a value between 1 and 12."}), 400
    except ValueError:
        return jsonify({"error": "Year and month must be integers."}), 400

    quarterly_data = {}
    for i in range(-1, 2):  # 이전 달, 현재 달, 다음 달 순서로 데이터를 가져오기
        month = (start_month + i - 1) % 12 + 1
        current_year = year + (start_month + i - 1) // 12
        monthly_data = get_monthly_data(current_year, month, user_id)
        quarterly_data[f"{current_year}-{str(month).zfill(2)}"] = monthly_data

    return jsonify(quarterly_data)

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5001)  # 다른 포트로 실행하여 send.py와 충돌 방지