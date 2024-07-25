from flask import Flask, request, jsonify
import pymysql
import os
from dotenv import load_dotenv
import logging
import calendar
from langchain.chat_models import AzureChatOpenAI
from langchain.schema import HumanMessage, SystemMessage

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

# Azure OpenAI 클라이언트 초기화
model = AzureChatOpenAI(
    azure_deployment=os.getenv("AZURE_OPENAI_DEPLOYMENT"),  # gpt-4o is set by env
    temperature=1.0
)

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

def get_advice(carbohydrates_percentage, protein_percentage, fat_percentage):
    try:
        # Chat API 호출
        messages = [
            SystemMessage(content="You are a nutrition expert providing dietary advice based on user's nutrient intake.Give 5 sentences of advice in Korean"),
            HumanMessage(content=f"Here are my monthly nutrient intake percentages:\n"
                                 f"Carbohydrates: {carbohydrates_percentage}%\n"
                                 f"Protein: {protein_percentage}%\n"
                                 f"Fat: {fat_percentage}%\n"
                                 f"Please provide advice on how to improve my diet")
        ]
        
        response = model(messages)
        
        # 응답 객체의 내용을 로그로 출력
        logging.debug(f"LLM Response Object: {response}")
        
        # 응답 내용을 추출
        response_content = response[0].content if isinstance(response, list) else response.content
        logging.debug(f"LLM Response Content: {response_content}")  # LLM 응답을 콘솔에 출력
        return response_content
    except Exception as e:
        logging.error(f"Error in get_advice: {e}")
        logging.debug(f"Carbohydrates: {carbohydrates_percentage}, Protein: {protein_percentage}, Fat: {fat_percentage}")  # 입력 데이터 디버깅
        return {"error": f"Failed to get advice from LLM: {str(e)}"}
    
@app.route('/api/food/advice', methods=['GET'])
def get_advice_route():
    year = request.args.get('year')
    month = request.args.get('month')
    user_id = request.args.get('user_id')

    if not year or not month or not user_id:
        return jsonify({"error": "Year, month, and user_id are required"}), 400

    try:
        year = int(year)
        month = int(month)
        if month < 1 or month > 12:
            return jsonify({"error": "Invalid month. Please enter a value between 1 and 12."}), 400
    except ValueError:
        return jsonify({"error": "Year and month must be integers."}), 400

    # 현재 달의 데이터를 가져옵니다
    monthly_data = get_monthly_data(year, month, user_id)

    if "error" in monthly_data:
        logging.error(f"Failed to get monthly data: {monthly_data['error']}")
        return jsonify(monthly_data), 500

    percentages_list = monthly_data['percentages']

    # 한 달치 평균 계산
    total_carbs = 0
    total_protein = 0
    total_fat = 0
    count = 0

    for day_data in percentages_list:
        if day_data:  # 빈 데이터는 건너뜀
            total_carbs += day_data.get('carbohydrates_percentage', 0)
            total_protein += day_data.get('protein_percentage', 0)
            total_fat += day_data.get('fat_percentage', 0)
            count += 1

    if count == 0:
        logging.error("No valid data to calculate averages")
        return jsonify({"error": "No valid data to calculate averages"}), 404

    average_carbs = total_carbs / count
    average_protein = total_protein / count
    average_fat = total_fat / count

    averages = {
        "average_carbohydrates_percentage": round(average_carbs, 1),
        "average_protein_percentage": round(average_protein, 1),
        "average_fat_percentage": round(average_fat, 1)
    }

    # LLM을 통해 조언을 받습니다
    advice = get_advice(averages["average_carbohydrates_percentage"],
                        averages["average_protein_percentage"],
                        averages["average_fat_percentage"])

    # 콘솔에 출력
    logging.debug(f"LLM Advice: {advice}")

    return jsonify({"averages": averages, "advice": advice})

@app.route('/api/food/avg_kcal', methods=['GET'])
def get_avg_kcal():
    year = request.args.get('year')
    month = request.args.get('month')
    user_id = request.args.get('user_id')

    if not year or not month or not user_id:
        return jsonify({"error": "Year, month, and user_id are required"}), 400

    try:
        year = int(year)
        month = int(month)
        if month < 1 or month > 12:
            return jsonify({"error": "Invalid month. Please enter a value between 1 and 12."}), 400
    except ValueError:
        return jsonify({"error": "Year and month must be integers."}), 400

    # 현재 달의 데이터를 가져옵니다
    monthly_data = get_monthly_data(year, month, user_id)

    if "error" in monthly_data:
        logging.error(f"Failed to get monthly data: {monthly_data['error']}")
        return jsonify(monthly_data), 500

    foods_list = monthly_data['foods']

    # 한 달치 평균 칼로리 계산
    total_kcal = 0
    count = 0

    for day_foods in foods_list:
        for food in day_foods:
            total_kcal += food.get('calories', 0)
            count += 1

    if count == 0:
        logging.error("No valid data to calculate averages")
        return jsonify({"error": "No valid data to calculate averages"}), 404

    average_kcal = total_kcal / count

    return jsonify({"average_kcal": round(average_kcal, 1)})

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5001)  # 다른 포트로