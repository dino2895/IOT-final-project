#!/bin/sh
set -e

# 等待 Nginx 啟動
sleep 5

# 嘗試獲取憑證
certbot --nginx --agree-tos --no-interactive -d iot.rm-rf.uk -m dino2895un@gmail.com

# 如果憑證不存在，則退出並顯示錯誤
if [ ! -f /etc/letsencrypt/live/iot.rm-rf.uk/fullchain.pem ]; then
    echo "憑證產生失敗，請檢查 Certbot 的輸出。"
    exit 1
fi

echo "憑證已成功產生或已存在。"

# 定期更新憑證 (可以將此命令放在後台運行或使用 cron)
# (sleep 3600 && certbot renew --nginx --agree-tos --no-interactive) &

# 啟動 Nginx
nginx -g 'daemon off;'