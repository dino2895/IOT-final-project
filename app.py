from flask import Flask, request, jsonify
import psycopg2
import os
from datetime import datetime, timedelta
import tensorflow as tf
import numpy as np


# 載入模型
classification_model = tf.keras.models.load_model('IOT_Model/badmiton_classification.keras')
speedestimate_model = tf.keras.models.load_model('IOT_Model/200_speed_estimate.keras')

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

@app.route('/inference', methods=['GET'])
def get_inference_data():
    device_id = request.args.get('device-id')
    end_timestamp = request.args.get('end-timestamp')

    if not end_timestamp:
        return jsonify({"error": "缺少 end-timestamp 參數"}), 400

    try:
        end_timestamp = datetime.fromisoformat(end_timestamp)
    except Exception as e:
        return jsonify({"error": f"end-timestamp 格式錯誤: {e}"}), 400

    start_timestamp = end_timestamp - timedelta(seconds=1)  # end_timestamp 前一秒

    conn = get_db_connection()
    if conn:
        cur = conn.cursor()
        try:
            # 第一次查詢：搜尋在指定時間範圍內 accel_y 絕對值最大的資料
            query = """
                SELECT id, device_id, mobile_timestamp, accel_x, accel_y, accel_z, gyro_x, gyro_y, gyro_z
                FROM sensor_data
                WHERE mobile_timestamp BETWEEN %s AND %s
                ORDER BY ABS(accel_y) DESC
                LIMIT 1
            """
            params = [start_timestamp, end_timestamp]
            if device_id:
                query += " AND device_id = %s"
                params.append(device_id)

            cur.execute(query, tuple(params))
            row = cur.fetchone()  # 取得第一筆資料
            if not row:
                return jsonify({"error": "在指定範圍內未找到資料"}), 404

            # 取得該筆資料的 mobile_timestamp
            target_timestamp = row[2]

            # 透過取得的target_timestamp查詢前 20 筆資料
            query_before = """
                SELECT id, device_id, mobile_timestamp, accel_x, accel_y, accel_z, gyro_x, gyro_y, gyro_z
                FROM sensor_data
                WHERE mobile_timestamp < %s
                ORDER BY mobile_timestamp DESC
                LIMIT 20
            """
            params_before = [target_timestamp]
            if device_id:
                query_before += " AND device_id = %s"
                params_before.append(device_id)

            cur.execute(query_before, tuple(params_before))
            rows_before = cur.fetchall()

            # 查詢後 9 筆資料
            query_after = """
                SELECT id, device_id, mobile_timestamp, accel_x, accel_y, accel_z, gyro_x, gyro_y, gyro_z
                FROM sensor_data
                WHERE mobile_timestamp > %s
                ORDER BY mobile_timestamp ASC
                LIMIT 9
            """
            params_after = [target_timestamp]
            if device_id:
                query_after += " AND device_id = %s"
                params_after.append(device_id)

            cur.execute(query_after, tuple(params_after))
            rows_after = cur.fetchall()

            # 合併這30筆資料
            data_list = [] #這個是包含device_id跟mobile_timestamp
            all_data = [] #這個沒有

            # 合併前 20 筆資料
            for row in rows_before:
                data_list.append({
                    "id": row[0],
                    "device_id": row[1],
                    "mobile_timestamp": row[2].isoformat(),
                    "accel_x": row[3],
                    "accel_y": row[4],
                    "accel_z": row[5],
                    "gyro_x": row[6],
                    "gyro_y": row[7],
                    "gyro_z": row[8]
                })
                all_data.append([row[3], row[4], row[5], row[6], row[7], row[8]])

            # 添加accel_y最大那筆
            data_list.append({
                "id": row[0],
                "device_id": row[1],
                "mobile_timestamp": row[2].isoformat(),
                "accel_x": row[3],
                "accel_y": row[4],
                "accel_z": row[5],
                "gyro_x": row[6],
                "gyro_y": row[7],
                "gyro_z": row[8]
            })
            all_data.append([row[3], row[4], row[5], row[6], row[7], row[8]])

            # 合併後 9 筆資料
            for row in rows_after:
                data_list.append({
                    "id": row[0],
                    "device_id": row[1],
                    "mobile_timestamp": row[2].isoformat(),
                    "accel_x": row[3],
                    "accel_y": row[4],
                    "accel_z": row[5],
                    "gyro_x": row[6],
                    "gyro_y": row[7],
                    "gyro_z": row[8]
                })
                all_data.append([row[3], row[4], row[5], row[6], row[7], row[8]])

            # 將要使用的資料轉換為 numpy 陣列，形狀為 (30, 6)
            all_data = np.array(all_data)

            # 調整形狀為 (1, 30, 6, 1)
            all_data_classification = all_data[np.newaxis, ..., np.newaxis]

            # 給分類模型進行推理
            classification_result = classification_model.predict(all_data_classification)

            # 調整 all_data shape 為 (1, 30, 6) 給 speedestimate_model
            all_data_speed = all_data[np.newaxis, ...]
            speed_result = speedestimate_model.predict(all_data_speed)

            # 回傳結果
            label_map = {
                0: "Clear",  # 高遠
                1: "Smash",  # 殺球
                2: "Drive",  # 平抽
                3: "Net",    # 網前
                4: "Lob",    # 挑球
                5: "Other"   # 其他
            }
            
            predicted_indices = apply_confidence_threshold(classification_result)
            predicted_labels = [label_map[i] for i in predicted_indices]
            speed_result = np.clip(speed_result, 20, 70)

            response = {
                # "data": data_list,
                "classification_prediction": predicted_labels,
                "speed_prediction": speed_result.tolist()
            }

            return jsonify(response), 200

        except psycopg2.Error as e:
            cur.close()
            conn.close()
            return jsonify({"error": f"讀取數據時發生錯誤: {e}"}), 500
    else:
        return jsonify({"error": "無法連接到資料庫"}), 500

def apply_confidence_threshold(pred_probs, threshold=0.6):
    max_probs = np.max(pred_probs, axis=1)
    predicted_labels = np.argmax(pred_probs, axis=1)
    predicted_labels[max_probs < threshold] = 5  # 將低信心的分類為 'Other'
    return predicted_labels

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