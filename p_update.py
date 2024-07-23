from flask import Flask, request, jsonify
import mysql.connector
from mysql.connector import Error
from dotenv import load_dotenv
import os

print("Loading .env file...")
load_dotenv()

db_host = os.getenv('DB_HOST')
db_name = os.getenv('DB_NAME')
db_user = os.getenv('DB_USER')
db_password = os.getenv('DB_PASSWORD')

# 환경 변수 확인을 위한 디버그 출력
print(f"DB_HOST: {db_host}")
print(f"DB_NAME: {db_name}")
print(f"DB_USER: {db_user}")
print(f"DB_PASSWORD: {db_password}")

app = Flask(__name__)

# 데이터베이스 연결 설정
def create_db_connection():
    try:
        print("Attempting to connect to the database...")
        connection = mysql.connector.connect(
            host=db_host,
            database=db_name,
            user=db_user,
            password=db_password
        )
        print("Database connection successful!")
        return connection
    except Error as e:
        print(f"Error connecting to MySQL database: {e}")
        return None

@app.route('/api/p_update', methods=['POST'])
def update_user():
    data = request.json
    
    if not data or 'id' not in data:
        return jsonify({"error": "Invalid data, 'id' is required"}), 400
    
    connection = create_db_connection()
    if not connection:
        return jsonify({"error": "Database connection failed"}), 500
    
    cursor = connection.cursor()
    
    try:
        update_query = "UPDATE USER SET "
        update_params = []
        
        for key, value in data.items():
            if key != 'id':
                update_query += f"{key} = %s, "
                update_params.append(value)
        
        update_query = update_query.rstrip(', ') + " WHERE ID = %s"
        update_params.append(data['id'])
        
        cursor.execute(update_query, tuple(update_params))
        connection.commit()
        
        return jsonify({"message": "User updated successfully"}), 200
    
    except Error as e:
        connection.rollback()
        return jsonify({"error": f"An error occurred: {str(e)}"}), 500
    
    finally:
        cursor.close()
        connection.close()

if __name__ == '__main__':
    app.run(debug=True)