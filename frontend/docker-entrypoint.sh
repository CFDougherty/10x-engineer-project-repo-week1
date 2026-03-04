#!/bin/sh
set -e

# Generate nginx config at startup so auth_basic is enabled only when
# API_KEY is set. Uses the same key as the backend — no extra variables.

AUTH_SECTION=""
if [ -n "$API_KEY" ]; then
    htpasswd -bc /etc/nginx/.htpasswd admin "$API_KEY"
    AUTH_SECTION='auth_basic "PromptLab"; auth_basic_user_file /etc/nginx/.htpasswd;'
fi

cat > /etc/nginx/conf.d/default.conf << EOF
server {
    listen 80;
    server_name localhost;

    ${AUTH_SECTION}

    location / {
        root /usr/share/nginx/html;
        index index.html index.htm;
        try_files \$uri \$uri/ /index.html;
    }

    location /api {
        proxy_pass http://backend:8000;
        proxy_set_header Host \$host;
        proxy_set_header X-Real-IP \$remote_addr;
        proxy_set_header X-Forwarded-For \$proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto \$scheme;
    }
}
EOF

exec nginx -g "daemon off;"
