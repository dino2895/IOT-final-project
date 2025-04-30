# 使用官方 Python 映像檔作為基礎映像檔
FROM python:alpine

# 設定工作目錄
WORKDIR /app

# 將 requirements.txt 複製到工作目錄
COPY requirements.txt .

# 安裝應用程式依賴
# RUN apt-get update && apt-get install -y libpq-dev gcc python3-dev
RUN pip install -r requirements.txt

# 將應用程式程式碼複製到工作目錄
COPY app.py .

# 設定環境變數 (如果你的 .env 檔案中有敏感資訊，不建議直接複製到映像檔中。
# 更好的做法是在運行容器時透過 Docker 的 --env 或 --env-file 傳遞)
# 如果你仍然想複製 .env，請取消註解下一行：
# COPY .env .

# 指定 Flask 應用程式啟動的命令
CMD ["flask", "run", "--host=0.0.0.0"]

# (可選) 暴露 Flask 應用程式預設的 5000 端口
EXPOSE 5000