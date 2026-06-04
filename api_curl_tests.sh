#!/usr/bin/env bash
set -u

if [ -f .env ]; then
  set -a
  # shellcheck disable=SC1091
  . ./.env
  set +a
fi

BASE="${BASE:-http://localhost:5001}"
STAMP="$(date +%s)"
LAST_BODY="$(mktemp)"
TEMP_PASSWORD="${TEMP_PASSWORD:-Temp-${STAMP}-Api!}"

ADMIN_EMAIL="${ADMIN_EMAIL:-}"
ADMIN_PASSWORD="${ADMIN_PASSWORD:-}"
MANAGER_EMAIL="${MANAGER_EMAIL:-}"
MANAGER_PASSWORD="${MANAGER_PASSWORD:-}"
CASHIER_EMAIL="${CASHIER_EMAIL:-}"
CASHIER_PASSWORD="${CASHIER_PASSWORD:-}"
CLIENT_EMAIL="${CLIENT_EMAIL:-}"
CLIENT_PASSWORD="${CLIENT_PASSWORD:-}"

cleanup() {
  rm -f "$LAST_BODY"
}
trap cleanup EXIT

require_command() {
  if ! command -v "$1" >/dev/null 2>&1; then
    echo "Не найдена команда: $1"
    echo "Установи её и запусти скрипт ещё раз."
    exit 1
  fi
}

require_env() {
  local name="$1"
  local value="$2"
  if [ -z "$value" ]; then
    echo "Не задана переменная окружения: $name"
    echo "Задай локальные данные перед запуском, например через .env или export."
    echo "Пример: export $name='<локальное значение>'"
    exit 1
  fi
}

print_header() {
  printf '\n\n========================================================================\n'
  printf '### %s\n' "$1"
}

request() {
  local label="$1"
  local display="$2"
  local filter="$3"
  shift 3

  print_header "$label"
  printf '$ %s\n' "$display"

  local code
  code="$(curl -sS "$@" -o "$LAST_BODY" -w "%{http_code}")"
  printf 'HTTP %s\n' "$code"

  if jq -e . "$LAST_BODY" >/dev/null 2>&1; then
    jq "$filter" "$LAST_BODY"
  else
    cat "$LAST_BODY"
  fi
}

token_filter='{
  message,
  user,
  access_token: (if .access_token then (.access_token[0:32] + "...") else null end),
  refresh_token: (if .refresh_token then (.refresh_token[0:32] + "...") else null end)
}'

require_command curl
require_command jq
require_env ADMIN_EMAIL "$ADMIN_EMAIL"
require_env ADMIN_PASSWORD "$ADMIN_PASSWORD"
require_env MANAGER_EMAIL "$MANAGER_EMAIL"
require_env MANAGER_PASSWORD "$MANAGER_PASSWORD"
require_env CASHIER_EMAIL "$CASHIER_EMAIL"
require_env CASHIER_PASSWORD "$CASHIER_PASSWORD"
require_env CLIENT_EMAIL "$CLIENT_EMAIL"
require_env CLIENT_PASSWORD "$CLIENT_PASSWORD"

if ! curl -fsS "$BASE/api/books" >/dev/null; then
  echo "Backend не отвечает: $BASE"
  echo "Сначала запусти проект:"
  echo "  docker compose up -d --build"
  exit 1
fi

json_header=(-H "Content-Type: application/json")

printf '\nСтарт curl-проверки API: %s\n' "$(date '+%Y-%m-%d %H:%M:%S')"
printf 'BASE=%s\n' "$BASE"

REGISTER_PAYLOAD="$(jq -nc --arg email "curl-user-$STAMP@example.com" --arg username "curl_user_$STAMP" --arg password "$TEMP_PASSWORD" '{email:$email, username:$username, password:$password, role:"client"}')"
request "POST /api/auth/register" \
  "curl -X POST $BASE/api/auth/register -H 'Content-Type: application/json' -d '{\"email\":\"curl-user-$STAMP@example.com\",\"username\":\"curl_user_$STAMP\",\"password\":\"<TEMP_PASSWORD>\",\"role\":\"client\"}'" \
  "$token_filter" \
  -X POST "$BASE/api/auth/register" "${json_header[@]}" -d "$REGISTER_PAYLOAD"
TEMP_USER_ID="$(jq -r '.user.id // empty' "$LAST_BODY")"

ADMIN_LOGIN_PAYLOAD="$(jq -nc --arg email "$ADMIN_EMAIL" --arg password "$ADMIN_PASSWORD" '{email:$email, password:$password}')"
request "POST /api/auth/login (admin)" \
  "curl -X POST $BASE/api/auth/login -H 'Content-Type: application/json' -d '{\"email\":\"$ADMIN_EMAIL\",\"password\":\"<ADMIN_PASSWORD>\"}'" \
  "$token_filter" \
  -X POST "$BASE/api/auth/login" "${json_header[@]}" -d "$ADMIN_LOGIN_PAYLOAD"
ADMIN_TOKEN="$(jq -r '.access_token // empty' "$LAST_BODY")"
ADMIN_REFRESH="$(jq -r '.refresh_token // empty' "$LAST_BODY")"

MANAGER_LOGIN_PAYLOAD="$(jq -nc --arg email "$MANAGER_EMAIL" --arg password "$MANAGER_PASSWORD" '{email:$email, password:$password}')"
request "POST /api/auth/login (manager)" \
  "curl -X POST $BASE/api/auth/login -H 'Content-Type: application/json' -d '{\"email\":\"$MANAGER_EMAIL\",\"password\":\"<MANAGER_PASSWORD>\"}'" \
  "$token_filter" \
  -X POST "$BASE/api/auth/login" "${json_header[@]}" -d "$MANAGER_LOGIN_PAYLOAD"
MANAGER_TOKEN="$(jq -r '.access_token // empty' "$LAST_BODY")"

CASHIER_LOGIN_PAYLOAD="$(jq -nc --arg email "$CASHIER_EMAIL" --arg password "$CASHIER_PASSWORD" '{email:$email, password:$password}')"
request "POST /api/auth/login (cashier)" \
  "curl -X POST $BASE/api/auth/login -H 'Content-Type: application/json' -d '{\"email\":\"$CASHIER_EMAIL\",\"password\":\"<CASHIER_PASSWORD>\"}'" \
  "$token_filter" \
  -X POST "$BASE/api/auth/login" "${json_header[@]}" -d "$CASHIER_LOGIN_PAYLOAD"
CASHIER_TOKEN="$(jq -r '.access_token // empty' "$LAST_BODY")"

CLIENT_LOGIN_PAYLOAD="$(jq -nc --arg email "$CLIENT_EMAIL" --arg password "$CLIENT_PASSWORD" '{email:$email, password:$password}')"
request "POST /api/auth/login (client)" \
  "curl -X POST $BASE/api/auth/login -H 'Content-Type: application/json' -d '{\"email\":\"$CLIENT_EMAIL\",\"password\":\"<CLIENT_PASSWORD>\"}'" \
  "$token_filter" \
  -X POST "$BASE/api/auth/login" "${json_header[@]}" -d "$CLIENT_LOGIN_PAYLOAD"
CLIENT_TOKEN="$(jq -r '.access_token // empty' "$LAST_BODY")"

request "GET /api/auth/me" \
  "curl -X GET $BASE/api/auth/me -H 'Authorization: Bearer \$ADMIN_TOKEN'" \
  '.' \
  -X GET "$BASE/api/auth/me" -H "Authorization: Bearer $ADMIN_TOKEN"

REFRESH_PAYLOAD="$(jq -nc --arg token "$ADMIN_REFRESH" '{refresh_token:$token}')"
request "POST /api/auth/refresh" \
  "curl -X POST $BASE/api/auth/refresh -H 'Content-Type: application/json' -d '{\"refresh_token\":\"...\"}'" \
  "$token_filter" \
  -X POST "$BASE/api/auth/refresh" "${json_header[@]}" -d "$REFRESH_PAYLOAD"

request "GET /api/users" \
  "curl -X GET $BASE/api/users -H 'Authorization: Bearer \$ADMIN_TOKEN'" \
  '{count:(.users|length), users:.users}' \
  -X GET "$BASE/api/users" -H "Authorization: Bearer $ADMIN_TOKEN"

request "GET /api/users/{user_id}" \
  "curl -X GET $BASE/api/users/$TEMP_USER_ID -H 'Authorization: Bearer \$ADMIN_TOKEN'" \
  '.' \
  -X GET "$BASE/api/users/$TEMP_USER_ID" -H "Authorization: Bearer $ADMIN_TOKEN"

request "PUT /api/users/{user_id}/role" \
  "curl -X PUT $BASE/api/users/$TEMP_USER_ID/role -H 'Authorization: Bearer \$ADMIN_TOKEN' -H 'Content-Type: application/json' -d '{\"role\":\"manager\"}'" \
  '.' \
  -X PUT "$BASE/api/users/$TEMP_USER_ID/role" -H "Authorization: Bearer $ADMIN_TOKEN" "${json_header[@]}" -d '{"role":"manager"}'

request "POST /api/users/{user_id}/deactivate" \
  "curl -X POST $BASE/api/users/$TEMP_USER_ID/deactivate -H 'Authorization: Bearer \$ADMIN_TOKEN'" \
  '.' \
  -X POST "$BASE/api/users/$TEMP_USER_ID/deactivate" -H "Authorization: Bearer $ADMIN_TOKEN"

request "POST /api/users/{user_id}/activate" \
  "curl -X POST $BASE/api/users/$TEMP_USER_ID/activate -H 'Authorization: Bearer \$ADMIN_TOKEN'" \
  '.' \
  -X POST "$BASE/api/users/$TEMP_USER_ID/activate" -H "Authorization: Bearer $ADMIN_TOKEN"

request "GET /api/users/admin-logs" \
  "curl -X GET '$BASE/api/users/admin-logs?limit=5' -H 'Authorization: Bearer \$ADMIN_TOKEN'" \
  '{count:(.logs|length), logs:.logs}' \
  -X GET "$BASE/api/users/admin-logs?limit=5" -H "Authorization: Bearer $ADMIN_TOKEN"

request "GET /api/users/activity-logs" \
  "curl -X GET '$BASE/api/users/activity-logs?limit=5' -H 'Authorization: Bearer \$ADMIN_TOKEN'" \
  '{count:(.logs|length), logs:.logs}' \
  -X GET "$BASE/api/users/activity-logs?limit=5" -H "Authorization: Bearer $ADMIN_TOKEN"

BOOK_PAYLOAD="$(jq -nc --arg isbn "CURL-$STAMP" '{title:"CURL demo book", title_ru:"Тестовая книга CURL", author:"Codex Tester", isbn:$isbn, price:123.45, publisher:"Demo", year:2026, description:"Temporary book for curl API screenshots", stock_quantity:20}')"
request "POST /api/books" \
  "curl -X POST $BASE/api/books -H 'Authorization: Bearer \$MANAGER_TOKEN' -H 'Content-Type: application/json' -d '$BOOK_PAYLOAD'" \
  '.' \
  -X POST "$BASE/api/books" -H "Authorization: Bearer $MANAGER_TOKEN" "${json_header[@]}" -d "$BOOK_PAYLOAD"
BOOK_ID="$(jq -r '.book.id // empty' "$LAST_BODY")"

request "GET /api/books" \
  "curl -X GET '$BASE/api/books?status=active'" \
  '{count:(.books|length), first_book:.books[0]}' \
  -X GET "$BASE/api/books?status=active"

request "GET /api/books/search" \
  "curl -X GET '$BASE/api/books/search?q=CURL'" \
  '{count:(.books|length), books:.books[:3]}' \
  -X GET "$BASE/api/books/search?q=CURL"

request "GET /api/books/{book_id}" \
  "curl -X GET $BASE/api/books/$BOOK_ID" \
  '.' \
  -X GET "$BASE/api/books/$BOOK_ID"

BOOK_UPDATE_PAYLOAD='{ "price": 150.00, "description": "Updated by curl test" }'
request "PUT /api/books/{book_id}" \
  "curl -X PUT $BASE/api/books/$BOOK_ID -H 'Authorization: Bearer \$MANAGER_TOKEN' -H 'Content-Type: application/json' -d '$BOOK_UPDATE_PAYLOAD'" \
  '.' \
  -X PUT "$BASE/api/books/$BOOK_ID" -H "Authorization: Bearer $MANAGER_TOKEN" "${json_header[@]}" -d "$BOOK_UPDATE_PAYLOAD"

request "GET /api/books/{book_id}/stock" \
  "curl -X GET $BASE/api/books/$BOOK_ID/stock" \
  '.' \
  -X GET "$BASE/api/books/$BOOK_ID/stock"

request "PUT /api/books/{book_id}/stock" \
  "curl -X PUT $BASE/api/books/$BOOK_ID/stock -H 'Authorization: Bearer \$MANAGER_TOKEN' -H 'Content-Type: application/json' -d '{\"quantity\":25}'" \
  '.' \
  -X PUT "$BASE/api/books/$BOOK_ID/stock" -H "Authorization: Bearer $MANAGER_TOKEN" "${json_header[@]}" -d '{"quantity":25}'

request "POST /api/books/{book_id}/stock/adjust" \
  "curl -X POST $BASE/api/books/$BOOK_ID/stock/adjust -H 'Authorization: Bearer \$MANAGER_TOKEN' -H 'Content-Type: application/json' -d '{\"quantity_change\":-1}'" \
  '.' \
  -X POST "$BASE/api/books/$BOOK_ID/stock/adjust" -H "Authorization: Bearer $MANAGER_TOKEN" "${json_header[@]}" -d '{"quantity_change":-1}'

request "POST /api/books/{book_id}/archive" \
  "curl -X POST $BASE/api/books/$BOOK_ID/archive -H 'Authorization: Bearer \$ADMIN_TOKEN'" \
  '.' \
  -X POST "$BASE/api/books/$BOOK_ID/archive" -H "Authorization: Bearer $ADMIN_TOKEN"

request "POST /api/books/{book_id}/restore" \
  "curl -X POST $BASE/api/books/$BOOK_ID/restore -H 'Authorization: Bearer \$ADMIN_TOKEN'" \
  '.' \
  -X POST "$BASE/api/books/$BOOK_ID/restore" -H "Authorization: Bearer $ADMIN_TOKEN"

CLIENT_PROFILE_PAYLOAD="$(jq -nc --arg email "$CLIENT_EMAIL" '{first_name:"Client", last_name:"Curl", phone:"+79991234567", email:$email}')"
request "PUT /api/clients/me" \
  "curl -X PUT $BASE/api/clients/me -H 'Authorization: Bearer \$CLIENT_TOKEN' -H 'Content-Type: application/json' -d '{\"first_name\":\"Client\",\"last_name\":\"Curl\",\"phone\":\"+79991234567\",\"email\":\"<CLIENT_EMAIL>\"}'" \
  '.' \
  -X PUT "$BASE/api/clients/me" -H "Authorization: Bearer $CLIENT_TOKEN" "${json_header[@]}" -d "$CLIENT_PROFILE_PAYLOAD"

request "GET /api/clients/me" \
  "curl -X GET $BASE/api/clients/me -H 'Authorization: Bearer \$CLIENT_TOKEN'" \
  '.' \
  -X GET "$BASE/api/clients/me" -H "Authorization: Bearer $CLIENT_TOKEN"

CLIENT_PAYLOAD="$(jq -nc --arg email "curl-client-$STAMP@example.com" '{first_name:"Curl", last_name:"Client", middle_name:"Demo", phone:"+79990001122", email:$email}')"
request "POST /api/clients" \
  "curl -X POST $BASE/api/clients -H 'Authorization: Bearer \$CASHIER_TOKEN' -H 'Content-Type: application/json' -d '$CLIENT_PAYLOAD'" \
  '.' \
  -X POST "$BASE/api/clients" -H "Authorization: Bearer $CASHIER_TOKEN" "${json_header[@]}" -d "$CLIENT_PAYLOAD"
CLIENT_ID="$(jq -r '.client.id // empty' "$LAST_BODY")"

request "GET /api/clients" \
  "curl -X GET $BASE/api/clients -H 'Authorization: Bearer \$CASHIER_TOKEN'" \
  '{count:(.clients|length), clients:.clients[:5]}' \
  -X GET "$BASE/api/clients" -H "Authorization: Bearer $CASHIER_TOKEN"

request "GET /api/clients/{client_id}" \
  "curl -X GET $BASE/api/clients/$CLIENT_ID -H 'Authorization: Bearer \$CASHIER_TOKEN'" \
  '.' \
  -X GET "$BASE/api/clients/$CLIENT_ID" -H "Authorization: Bearer $CASHIER_TOKEN"

request "PUT /api/clients/{client_id}" \
  "curl -X PUT $BASE/api/clients/$CLIENT_ID -H 'Authorization: Bearer \$MANAGER_TOKEN' -H 'Content-Type: application/json' -d '{\"first_name\":\"CurlUpdated\",\"last_name\":\"ClientUpdated\"}'" \
  '.' \
  -X PUT "$BASE/api/clients/$CLIENT_ID" -H "Authorization: Bearer $MANAGER_TOKEN" "${json_header[@]}" -d '{"first_name":"CurlUpdated","last_name":"ClientUpdated"}'

ORDER_PAYLOAD="$(jq -nc --argjson book_id "$BOOK_ID" '{items:[{book_id:$book_id, quantity:1}], customer_comment:"curl order"}')"
request "POST /api/orders/checkout (for approve)" \
  "curl -X POST $BASE/api/orders/checkout -H 'Authorization: Bearer \$CLIENT_TOKEN' -H 'Content-Type: application/json' -d '$ORDER_PAYLOAD'" \
  '.' \
  -X POST "$BASE/api/orders/checkout" -H "Authorization: Bearer $CLIENT_TOKEN" "${json_header[@]}" -d "$ORDER_PAYLOAD"
ORDER_APPROVE_ID="$(jq -r '.order.id // empty' "$LAST_BODY")"

request "POST /api/orders/checkout (for reject)" \
  "curl -X POST $BASE/api/orders/checkout -H 'Authorization: Bearer \$CLIENT_TOKEN' -H 'Content-Type: application/json' -d '$ORDER_PAYLOAD'" \
  '.' \
  -X POST "$BASE/api/orders/checkout" -H "Authorization: Bearer $CLIENT_TOKEN" "${json_header[@]}" -d "$ORDER_PAYLOAD"
ORDER_REJECT_ID="$(jq -r '.order.id // empty' "$LAST_BODY")"

request "POST /api/orders/checkout (for cancel)" \
  "curl -X POST $BASE/api/orders/checkout -H 'Authorization: Bearer \$CLIENT_TOKEN' -H 'Content-Type: application/json' -d '$ORDER_PAYLOAD'" \
  '.' \
  -X POST "$BASE/api/orders/checkout" -H "Authorization: Bearer $CLIENT_TOKEN" "${json_header[@]}" -d "$ORDER_PAYLOAD"
ORDER_CANCEL_ID="$(jq -r '.order.id // empty' "$LAST_BODY")"

request "GET /api/orders/my" \
  "curl -X GET $BASE/api/orders/my -H 'Authorization: Bearer \$CLIENT_TOKEN'" \
  '{count:(.orders|length), orders:.orders[:5]}' \
  -X GET "$BASE/api/orders/my" -H "Authorization: Bearer $CLIENT_TOKEN"

request "GET /api/orders" \
  "curl -X GET '$BASE/api/orders?status=all' -H 'Authorization: Bearer \$MANAGER_TOKEN'" \
  '{count:(.orders|length), orders:.orders[:5]}' \
  -X GET "$BASE/api/orders?status=all" -H "Authorization: Bearer $MANAGER_TOKEN"

request "POST /api/orders/{order_id}/approve" \
  "curl -X POST $BASE/api/orders/$ORDER_APPROVE_ID/approve -H 'Authorization: Bearer \$MANAGER_TOKEN' -H 'Content-Type: application/json' -d '{\"manager_comment\":\"Approved by curl\"}'" \
  '.' \
  -X POST "$BASE/api/orders/$ORDER_APPROVE_ID/approve" -H "Authorization: Bearer $MANAGER_TOKEN" "${json_header[@]}" -d '{"manager_comment":"Approved by curl"}'

request "POST /api/orders/{order_id}/reject" \
  "curl -X POST $BASE/api/orders/$ORDER_REJECT_ID/reject -H 'Authorization: Bearer \$MANAGER_TOKEN' -H 'Content-Type: application/json' -d '{\"manager_comment\":\"Rejected by curl\"}'" \
  '.' \
  -X POST "$BASE/api/orders/$ORDER_REJECT_ID/reject" -H "Authorization: Bearer $MANAGER_TOKEN" "${json_header[@]}" -d '{"manager_comment":"Rejected by curl"}'

request "POST /api/orders/{order_id}/cancel" \
  "curl -X POST $BASE/api/orders/$ORDER_CANCEL_ID/cancel -H 'Authorization: Bearer \$CLIENT_TOKEN'" \
  '.' \
  -X POST "$BASE/api/orders/$ORDER_CANCEL_ID/cancel" -H "Authorization: Bearer $CLIENT_TOKEN"

SALE_PAYLOAD="$(jq -nc --argjson book_id "$BOOK_ID" '{items:[{book_id:$book_id, quantity:1}]}')"
request "POST /api/sales (for return)" \
  "curl -X POST $BASE/api/sales -H 'Authorization: Bearer \$CASHIER_TOKEN' -H 'Content-Type: application/json' -d '$SALE_PAYLOAD'" \
  '.' \
  -X POST "$BASE/api/sales" -H "Authorization: Bearer $CASHIER_TOKEN" "${json_header[@]}" -d "$SALE_PAYLOAD"
SALE_RETURN_ID="$(jq -r '.sale.id // empty' "$LAST_BODY")"

request "POST /api/sales (for cancel)" \
  "curl -X POST $BASE/api/sales -H 'Authorization: Bearer \$CASHIER_TOKEN' -H 'Content-Type: application/json' -d '$SALE_PAYLOAD'" \
  '.' \
  -X POST "$BASE/api/sales" -H "Authorization: Bearer $CASHIER_TOKEN" "${json_header[@]}" -d "$SALE_PAYLOAD"
SALE_CANCEL_ID="$(jq -r '.sale.id // empty' "$LAST_BODY")"

request "GET /api/sales" \
  "curl -X GET $BASE/api/sales -H 'Authorization: Bearer \$MANAGER_TOKEN'" \
  '{count:(.sales|length), sales:.sales[:5]}' \
  -X GET "$BASE/api/sales" -H "Authorization: Bearer $MANAGER_TOKEN"

request "GET /api/sales/{sale_id}" \
  "curl -X GET $BASE/api/sales/$SALE_RETURN_ID -H 'Authorization: Bearer \$CASHIER_TOKEN'" \
  '.' \
  -X GET "$BASE/api/sales/$SALE_RETURN_ID" -H "Authorization: Bearer $CASHIER_TOKEN"

request "POST /api/sales/{sale_id}/return" \
  "curl -X POST $BASE/api/sales/$SALE_RETURN_ID/return -H 'Authorization: Bearer \$CASHIER_TOKEN'" \
  '.' \
  -X POST "$BASE/api/sales/$SALE_RETURN_ID/return" -H "Authorization: Bearer $CASHIER_TOKEN"

request "POST /api/sales/{sale_id}/cancel" \
  "curl -X POST $BASE/api/sales/$SALE_CANCEL_ID/cancel -H 'Authorization: Bearer \$MANAGER_TOKEN'" \
  '.' \
  -X POST "$BASE/api/sales/$SALE_CANCEL_ID/cancel" -H "Authorization: Bearer $MANAGER_TOKEN"

request "GET /api/reports/sales" \
  "curl -X GET '$BASE/api/reports/sales?status=COMPLETED' -H 'Authorization: Bearer \$MANAGER_TOKEN'" \
  '.' \
  -X GET "$BASE/api/reports/sales?status=COMPLETED" -H "Authorization: Bearer $MANAGER_TOKEN"

request "GET /api/reports/sales/top-books" \
  "curl -X GET '$BASE/api/reports/sales/top-books?limit=3' -H 'Authorization: Bearer \$MANAGER_TOKEN'" \
  '.' \
  -X GET "$BASE/api/reports/sales/top-books?limit=3" -H "Authorization: Bearer $MANAGER_TOKEN"

request "GET /api/reports/stock" \
  "curl -X GET $BASE/api/reports/stock -H 'Authorization: Bearer \$MANAGER_TOKEN'" \
  '{total_books,total_value, low_stock_count:(.low_stock_books|length), out_of_stock_count:(.out_of_stock_books|length)}' \
  -X GET "$BASE/api/reports/stock" -H "Authorization: Bearer $MANAGER_TOKEN"

request "GET /api/reports/cashier/{cashier_id}" \
  "curl -X GET $BASE/api/reports/cashier/10 -H 'Authorization: Bearer \$MANAGER_TOKEN'" \
  '.' \
  -X GET "$BASE/api/reports/cashier/10" -H "Authorization: Bearer $MANAGER_TOKEN"

REC_PAYLOAD="$(jq -nc --argjson book_id "$BOOK_ID" '{cart_book_ids:[$book_id], limit:3}')"
request "POST /api/recommendations/cart" \
  "curl -X POST $BASE/api/recommendations/cart -H 'Content-Type: application/json' -d '$REC_PAYLOAD'" \
  '{count:(.recommendations|length), recommendations:.recommendations[:3]}' \
  -X POST "$BASE/api/recommendations/cart" "${json_header[@]}" -d "$REC_PAYLOAD"

request "GET /api/recommendations/history" \
  "curl -X GET '$BASE/api/recommendations/history?limit=3' -H 'Authorization: Bearer \$CLIENT_TOKEN'" \
  '{count:(.recommendations|length), recommendations:.recommendations[:3]}' \
  -X GET "$BASE/api/recommendations/history?limit=3" -H "Authorization: Bearer $CLIENT_TOKEN"

request "GET /api/recommendations/personal" \
  "curl -X GET '$BASE/api/recommendations/personal?limit=3&cart_book_ids=$BOOK_ID' -H 'Authorization: Bearer \$CLIENT_TOKEN'" \
  '{count:(.recommendations|length), recommendations:.recommendations[:3]}' \
  -X GET "$BASE/api/recommendations/personal?limit=3&cart_book_ids=$BOOK_ID" -H "Authorization: Bearer $CLIENT_TOKEN"

request "GET /api/recommendations/popular" \
  "curl -X GET '$BASE/api/recommendations/popular?limit=3'" \
  '{count:(.popular_books|length), popular_books:.popular_books[:3]}' \
  -X GET "$BASE/api/recommendations/popular?limit=3"

request "POST /api/recommendations/sets" \
  "curl -X POST $BASE/api/recommendations/sets -H 'Content-Type: application/json' -d '$REC_PAYLOAD'" \
  '{count:(.recommendations|length), recommendations:.recommendations[:3]}' \
  -X POST "$BASE/api/recommendations/sets" "${json_header[@]}" -d "$REC_PAYLOAD"

QUESTION_PAYLOAD="$(jq -nc --arg email "curl-question-$STAMP@example.com" '{name:"Curl Client", email:$email, phone:"+79991112233", topic:"API test", message:"Question from curl test"}')"
request "POST /api/questions" \
  "curl -X POST $BASE/api/questions -H 'Authorization: Bearer \$CLIENT_TOKEN' -H 'Content-Type: application/json' -d '$QUESTION_PAYLOAD'" \
  '.' \
  -X POST "$BASE/api/questions" -H "Authorization: Bearer $CLIENT_TOKEN" "${json_header[@]}" -d "$QUESTION_PAYLOAD"

request "GET /api/questions" \
  "curl -X GET '$BASE/api/questions?status=all' -H 'Authorization: Bearer \$MANAGER_TOKEN'" \
  '{count:(.questions|length), questions:.questions[:5]}' \
  -X GET "$BASE/api/questions?status=all" -H "Authorization: Bearer $MANAGER_TOKEN"

request "DELETE /api/clients/{client_id}" \
  "curl -X DELETE $BASE/api/clients/$CLIENT_ID -H 'Authorization: Bearer \$MANAGER_TOKEN'" \
  '.' \
  -X DELETE "$BASE/api/clients/$CLIENT_ID" -H "Authorization: Bearer $MANAGER_TOKEN"

request "DELETE /api/users/{user_id}" \
  "curl -X DELETE $BASE/api/users/$TEMP_USER_ID -H 'Authorization: Bearer \$ADMIN_TOKEN'" \
  '.' \
  -X DELETE "$BASE/api/users/$TEMP_USER_ID" -H "Authorization: Bearer $ADMIN_TOKEN"

request "CLEANUP: POST /api/books/{book_id}/archive" \
  "curl -X POST $BASE/api/books/$BOOK_ID/archive -H 'Authorization: Bearer \$ADMIN_TOKEN'" \
  '.' \
  -X POST "$BASE/api/books/$BOOK_ID/archive" -H "Authorization: Bearer $ADMIN_TOKEN"

request "POST /api/auth/logout" \
  "curl -X POST $BASE/api/auth/logout -H 'Authorization: Bearer \$ADMIN_TOKEN'" \
  '.' \
  -X POST "$BASE/api/auth/logout" -H "Authorization: Bearer $ADMIN_TOKEN"

printf '\n\nГотово: curl-проверка завершена: %s\n' "$(date '+%Y-%m-%d %H:%M:%S')"
