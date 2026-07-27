#!/bin/sh
set -eu

API_BASE_URL="${API_BASE_URL:-/}"
cat > /app/dist/nexus-agent-ui/assets/config.js <<EOF
window.__APP_CONFIG__ = window.__APP_CONFIG__ || {};
window.__APP_CONFIG__.apiBaseUrl = '${API_BASE_URL}';
EOF

npx serve -s /app/dist/nexus-agent-ui -l "${PORT:-4200}"
