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
    """接收來自感測器的 POST 請求並批次儲存數據到資料庫。"""
    if not request.is_json:
        return jsonify({"error": "請求必須是 JSON 格式"}), 400

    data = request.get_json()

    # 確保接收到的是一個列表
    if not isinstance(data, list):
        return jsonify({"error": "請求的資料必須是 JSON 陣列"}), 400

    # 驗證每筆資料是否包含必要的欄位
    required_fields = ['device_id', 'TimeStamp', 'accel_x', 'accel_y', 'accel_z', 'gyro_x', 'gyro_y', 'gyro_z']
    for record in data:
        if not all(field in record for field in required_fields):
            return jsonify({"error": "每筆資料必須包含必要的欄位 (包括 TimeStamp)"}), 400

    # 準備批次插入的資料
    records_to_insert = []
    for record in data:
        try:
            # 假設 TimeStamp 是 ISO 8601 格式的字串，例如 "2025-04-24T07:46:00Z" (UTC)
            mobile_timestamp = datetime.fromisoformat(record['TimeStamp'].replace('Z', '+00:00'))
            records_to_insert.append((
                record['device_id'],
                mobile_timestamp,
                record['accel_x'],
                record['accel_y'],
                record['accel_z'],
                record['gyro_x'],
                record['gyro_y'],
                record['gyro_z']
            ))
        except ValueError as ve:
            return jsonify({"error": f"TimeStamp 格式錯誤: {ve}"}), 400

    # 將資料批次插入資料庫
    conn = get_db_connection()
    if conn:
        cur = conn.cursor()
        try:
            cur.executemany("""
                INSERT INTO sensor_data (device_id, mobile_timestamp, accel_x, accel_y, accel_z, gyro_x, gyro_y, gyro_z)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
            """, records_to_insert)
            conn.commit()
            cur.close()
            conn.close()
            return jsonify({"message": f"{len(records_to_insert)} 筆數據已成功儲存"}), 201
        except psycopg2.Error as e:
            conn.rollback()
            cur.close()
            conn.close()
            return jsonify({"error": f"儲存數據時發生錯誤: {e}"}), 500
    else:
        return jsonify({"error": "無法連接到資料庫"}), 500

@app.route('/sensor_data', methods=['GET'])
def get_sensor_data():
    """讀取資料庫中的感測器數據，可以根據 device_id 和 timestamp 篩選。"""
    # 優先從 URL query string 取得 device_id 和 timestamp
    device_id = request.args.get('device_id')
    start_timestamp = request.args.get('start_timestamp')  # 篩選的起始時間
    end_timestamp = request.args.get('end_timestamp')      # 篩選的結束時間

    # 如果 query string 沒有提供 device_id，則嘗試從 JSON body 取得
    if not device_id or not start_timestamp or not end_timestamp:
        if request.is_json:
            data = request.get_json()
            device_id = data.get('device_id', device_id)
            start_timestamp = data.get('start_timestamp', start_timestamp)
            end_timestamp = data.get('end_timestamp', end_timestamp)

    conn = get_db_connection()
    if conn:
        cur = conn.cursor()
        try:
            # 根據是否提供 device_id 和 timestamp 篩選條件動態生成 SQL 查詢
            query = """
                SELECT id, device_id, mobile_timestamp, accel_x, accel_y, accel_z, gyro_x, gyro_y, gyro_z
                FROM sensor_data
            """
            conditions = []
            params = []

            if device_id:
                conditions.append("device_id = %s")
                params.append(device_id)
            if start_timestamp:
                conditions.append("mobile_timestamp >= %s")
                params.append(start_timestamp)
            if end_timestamp:
                conditions.append("mobile_timestamp <= %s")
                params.append(end_timestamp)

            if conditions:
                query += " WHERE " + " AND ".join(conditions)
            query += " ORDER BY mobile_timestamp DESC"

            cur.execute(query, tuple(params))
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