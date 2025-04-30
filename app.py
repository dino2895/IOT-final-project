from flask import Flask, request, jsonify
import psycopg2
import os
from datetime import datetime

app = Flask(__name__)

# 資料庫連線設定 (建議使用環境變數管理敏感資訊)
DB_HOST = os.environ.get('DB_HOST', 'your_db_host')
DB_NAME = os.environ.get('DB_NAME', 'your_db_name')
DB_USER = os.environ.get('DB_USER', 'your_db_user')
DB_PASSWORD = os.environ.get('DB_PASSWORD', 'your_db_password')

def get_db_connection():
    """建立並返回資料庫連線。"""
    conn = None
    try:
        conn = psycopg2.connect(host=DB_HOST,
                                database=DB_NAME,
                                user=DB_USER,
                                password=DB_PASSWORD)
    except psycopg2.Error as e:
        print(f"無法連接到資料庫: {e}")
    return conn

@app.route('/sensor_data', methods=['POST'])
def receive_sensor_data():
    """接收來自感測器的 POST 請求並儲存數據到資料庫。"""
    if not request.is_json:
        return jsonify({"error": "請求必須是 JSON 格式"}), 400

    data = request.get_json()

    # 驗證接收到的資料是否包含必要的欄位，包括 TimeStamp
    required_fields = ['device_id', 'TimeStamp', 'accel_x', 'accel_y', 'accel_z', 'gyro_x', 'gyro_y', 'gyro_z']
    if not all(field in data for field in required_fields):
        return jsonify({"error": "請求缺少必要的欄位 (包括 TimeStamp)"}), 400

    device_id = data['device_id']
    mobile_timestamp_str = data['TimeStamp']
    accel_x = data['accel_x']
    accel_y = data['accel_y']
    accel_z = data['accel_z']
    gyro_x = data['gyro_x']
    gyro_y = data['gyro_y']
    gyro_z = data['gyro_z']

    conn = get_db_connection()
    if conn:
        cur = conn.cursor()
        try:
            # 假設 TimeStamp 是 ISO 8601 格式的字串，例如 "2025-04-24T07:46:00Z" (UTC)
            # 或者包含時區資訊，例如 "2025-04-24T15:46:00+08:00" (台灣時間)
            mobile_timestamp = datetime.fromisoformat(mobile_timestamp_str.replace('Z', '+00:00'))
            # 如果手機端發送的是 Unix 時間戳 (秒)，則可以使用以下方式轉換
            # mobile_timestamp = datetime.utcfromtimestamp(float(mobile_timestamp_str))

            cur.execute("""
                INSERT INTO sensor_data (device_id, mobile_timestamp, accel_x, accel_y, accel_z, gyro_x, gyro_y, gyro_z)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
            """, (device_id, mobile_timestamp, accel_x, accel_y, accel_z, gyro_x, gyro_y, gyro_z))
            conn.commit()
            cur.close()
            conn.close()
            return jsonify({"message": "數據已成功儲存"}), 201
        except ValueError as ve:
            conn.rollback()
            cur.close()
            conn.close()
            return jsonify({"error": f"TimeStamp 格式錯誤: {ve}"}), 400
        except psycopg2.Error as e:
            conn.rollback()
            cur.close()
            conn.close()
            return jsonify({"error": f"儲存數據時發生錯誤: {e}"}), 500
    else:
        return jsonify({"error": "無法連接到資料庫"}), 500

@app.route('/sensor_data', methods=['GET'])
def get_sensor_data():
    """讀取資料庫中的感測器數據，可以根據 device_id 過濾。"""
    device_id = request.args.get('device_id')  # 從 URL query string 取得 device_id，例如 /get_sensor_data?device_id=abc123

    conn = get_db_connection()
    if conn:
        cur = conn.cursor()
        try:
            if device_id:
                cur.execute("""
                    SELECT id, device_id, mobile_timestamp, accel_x, accel_y, accel_z, gyro_x, gyro_y, gyro_z
                    FROM sensor_data
                    WHERE device_id = %s
                    ORDER BY mobile_timestamp DESC
                """, (device_id,))
            else:
                cur.execute("""
                    SELECT id, device_id, mobile_timestamp, accel_x, accel_y, accel_z, gyro_x, gyro_y, gyro_z
                    FROM sensor_data
                    ORDER BY mobile_timestamp DESC
                """)
            
            rows = cur.fetchall()
            cur.close()
            conn.close()

            # 將查詢結果轉成 JSON 格式
            data_list = []
            for row in rows:
                data_list.append({
                    "id": row[0],
                    "device_id": row[1],
                    "mobile_timestamp": row[2].isoformat(),  # datetime 轉成 ISO 格式字串
                    "accel_x": row[3],
                    "accel_y": row[4],
                    "accel_z": row[5],
                    "gyro_x": row[6],
                    "gyro_y": row[7],
                    "gyro_z": row[8]
                })

            return jsonify(data_list), 200
        except psycopg2.Error as e:
            cur.close()
            conn.close()
            return jsonify({"error": f"讀取數據時發生錯誤: {e}"}), 500
    else:
        return jsonify({"error": "無法連接到資料庫"}), 500
    
@app.route('/health', methods=['GET'])
def health_check():
    """提供 ECS 的 Health Check API，回傳 200 OK"""
    return jsonify({"status": "ok"}), 200

@app.route('/ping', methods=['GET'])
def ping():
    """簡單測試用 API，回傳 'pong'"""
    return jsonify({"message": "pong"}), 200

@app.route('/', methods=['GET'])
def slash():
    return jsonify({"message": "ok"}), 200

# @app.route('/debug_db', methods=['GET'])
# def debug_db():
#     """測試資料庫連線，顯示目前的連線參數與錯誤訊息"""
#     response = {
#         "DB_HOST": DB_HOST,
#         "DB_NAME": DB_NAME,
#         "DB_USER": DB_USER,
#         "status": "unknown",
#         "error": None
#     }
#     try:
#         conn = psycopg2.connect(
#             host=DB_HOST,
#             database=DB_NAME,
#             user=DB_USER,
#             password=DB_PASSWORD
#         )
#         cur = conn.cursor()
#         cur.execute('SELECT version();')
#         version = cur.fetchone()
#         cur.close()
#         conn.close()
#         response["status"] = "connected"
#         response["db_version"] = version[0]
#         return jsonify(response), 200
#     except psycopg2.OperationalError as e:
#         response["status"] = "connection_failed"
#         response["error"] = str(e)
#         return jsonify(response), 500


if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5000)