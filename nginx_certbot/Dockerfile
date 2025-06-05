# 使用官方 Nginx 映像檔作為基礎映像檔
FROM nginx:stable-alpine

# 安裝 Certbot 及其 Nginx 外掛
RUN apk add --no-cache certbot certbot-nginx

# 移除預設的 Nginx 設定檔
RUN rm /etc/nginx/conf.d/default.conf

# 將你的 Nginx 設定檔複製到容器中
COPY nginx.conf /etc/nginx/conf.d/
COPY nginx.conf /etc/nginx/conf.d/default.conf

# 設定 Certbot 運行的腳本
COPY certbot_run.sh /usr/local/bin/
RUN chmod +x /usr/local/bin/certbot_run.sh

# 定義憑證和配置的卷 (Volumes)
VOLUME /etc/letsencrypt
VOLUME /var/www/html

# 設定容器啟動時執行的命令
# 這裡先啟動 Nginx，然後運行 Certbot 嘗試獲取憑證
CMD ["/bin/sh", "-c", "/usr/local/bin/certbot_run.sh && nginx -g 'daemon off;'"]

# 暴露 80 和 443 端口
EXPOSE 80
EXPOSE 443