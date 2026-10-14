#!/usr/bin/env bash
# ==============================================================================
# SEI MCP Server Automated cURL Test Suite
#
# Tests both StreamableHTTP (/mcp) and SSE (/sse + /messages) transports,
# as well as Health (/health) and OAuth 2.0 discovery endpoints (/.well-known/*).
#
# Usage:
#   ./scripts/test-mcp-curl.sh [options]
#
# Options:
#   --url, -u <URL>       Base URL of the MCP server (default: http://localhost:3000)
#   --token, -t <TOKEN>   OAuth 2.0 Bearer Token (optional)
#   --gcloud-auth         Fetch Bearer token automatically using 'gcloud auth print-access-token'
#   --verbose, -v         Print full request and response payloads
#   --help, -h            Show this help message
# ==============================================================================

set -o pipefail

# Bypass corporate/environment HTTP proxies when testing localhost/127.0.0.1
export NO_PROXY="${NO_PROXY:+$NO_PROXY,}127.0.0.1,localhost"
export no_proxy="${no_proxy:+$no_proxy,}127.0.0.1,localhost"

BASE_URL="http://localhost:3000"
TOKEN=""
VERBOSE=false
USE_GCLOUD_AUTH=false

# Colors
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
CYAN='\033[0;36m'
BOLD='\033[1m'
NC='\033[0m' # No Color

# Counters
TOTAL_TESTS=0
PASSED_TESTS=0
FAILED_TESTS=0

# Parse arguments
while [[ "$#" -gt 0 ]]; do
  case $1 in
    --url|-u)
      BASE_URL="${2%/}"
      shift 2
      ;;
    --token|-t)
      TOKEN="$2"
      shift 2
      ;;
    --gcloud-auth)
      USE_GCLOUD_AUTH=true
      shift
      ;;
    --verbose|-v)
      VERBOSE=true
      shift
      ;;
    --help|-h)
      echo "Usage: $0 [options]"
      echo ""
      echo "Options:"
      echo "  --url, -u <URL>       Base URL of the MCP server (default: http://localhost:3000)"
      echo "  --token, -t <TOKEN>   OAuth 2.0 Bearer Token"
      echo "  --gcloud-auth         Use 'gcloud auth print-access-token' to get an OAuth token"
      echo "  --verbose, -v         Print request & response details"
      echo "  --help, -h            Show this help message"
      exit 0
      ;;
    *)
      echo "Unknown parameter: $1"
      exit 1
      ;;
  esac
done

if [ "$USE_GCLOUD_AUTH" = true ]; then
  if command -v gcloud &> /dev/null; then
    echo -e "${CYAN}🔑 Obtaining OAuth token via gcloud...${NC}"
    TOKEN=$(gcloud auth print-access-token 2>/dev/null || true)
    if [ -n "$TOKEN" ]; then
      echo -e "${GREEN}✓ Successfully retrieved gcloud access token${NC}"
    else
      echo -e "${YELLOW}⚠️ Failed to get gcloud token. Proceeding unauthenticated.${NC}"
    fi
  else
    echo -e "${YELLOW}⚠️ 'gcloud' CLI not found. Proceeding without OAuth token.${NC}"
  fi
fi

# Helper: Extract JSON payload from plain JSON or SSE data streams
extract_json() {
  local raw="$1"
  if echo "$raw" | grep -q '^data: '; then
    echo "$raw" | grep '^data: ' | head -n1 | sed 's/^data: //'
  else
    echo "$raw"
  fi
}

# Assert function
assert_test() {
  local test_name="$1"
  local expected_status="$2"
  local actual_status="$3"
  local body="$4"
  local json_query="${5:-}"

  TOTAL_TESTS=$((TOTAL_TESTS + 1))
  echo -ne "  [Test $TOTAL_TESTS] $test_name ... "

  local status_matched=false
  IFS='|' read -ra ALLOWED_CODES <<< "$expected_status"
  for code in "${ALLOWED_CODES[@]}"; do
    if [ "$actual_status" -eq "$code" ]; then
      status_matched=true
      break
    fi
  done

  if [ "$status_matched" = false ]; then
    echo -e "${RED}FAILED (Expected HTTP $expected_status, got $actual_status)${NC}"
    FAILED_TESTS=$((FAILED_TESTS + 1))
    if [ "$VERBOSE" = true ]; then
      echo -e "    ${YELLOW}Response Body:${NC} $body"
    fi
    return
  fi

  local json_body
  json_body=$(extract_json "$body")

  if [ -n "$json_query" ] && command -v jq &> /dev/null; then
    local query_result
    query_result=$(echo "$json_body" | jq -e "$json_query" 2>/dev/null || true)
    if [ "$query_result" = "false" ] || [ "$query_result" = "null" ] || [ -z "$query_result" ]; then
      echo -e "${RED}FAILED (JSON query '$json_query' assertion failed)${NC}"
      FAILED_TESTS=$((FAILED_TESTS + 1))
      if [ "$VERBOSE" = true ]; then
        echo -e "    ${YELLOW}Extracted JSON:${NC} $json_body"
      fi
      return
    fi
  fi

  echo -e "${GREEN}PASSED (HTTP $actual_status)${NC}"
  PASSED_TESTS=$((PASSED_TESTS + 1))
  if [ "$VERBOSE" = true ]; then
    echo -e "    ${CYAN}Extracted JSON:${NC} $json_body"
  fi
}

echo -e "\n${BOLD}======================================================${NC}"
echo -e "${BOLD}🧪 SEI MCP Server (Python) cURL Test Suite${NC}"
echo -e "Target URL: ${BLUE}$BASE_URL${NC}"
if [ -n "$TOKEN" ]; then
  echo -e "Auth Token: ${GREEN}Bearer [Configured]${NC}"
else
  echo -e "Auth Token: ${YELLOW}None (Unauthenticated mode)${NC}"
fi
echo -e "${BOLD}======================================================${NC}\n"

# ------------------------------------------------------------------------------
# Section 1: Health & OAuth Discovery Endpoints
# ------------------------------------------------------------------------------
echo -e "${BOLD}📡 1. Testing Health & Discovery Endpoints${NC}"

HEALTH_RESP=$(curl -s -w "\n%{http_code}" "$BASE_URL/health")
HEALTH_CODE=$(echo "$HEALTH_RESP" | tail -n1)
HEALTH_BODY=$(echo "$HEALTH_RESP" | sed '$d')
assert_test "GET /health (Liveness Probe)" "200" "$HEALTH_CODE" "$HEALTH_BODY" '.status == "healthy"'

PR_RESP=$(curl -s -w "\n%{http_code}" "$BASE_URL/.well-known/oauth-protected-resource")
PR_CODE=$(echo "$PR_RESP" | tail -n1)
PR_BODY=$(echo "$PR_RESP" | sed '$d')
assert_test "GET /.well-known/oauth-protected-resource" "200" "$PR_CODE" "$PR_BODY" '.authorization_servers | length > 0'

AS_RESP=$(curl -s -w "\n%{http_code}" "$BASE_URL/.well-known/oauth-authorization-server")
AS_CODE=$(echo "$AS_RESP" | tail -n1)
AS_BODY=$(echo "$AS_RESP" | sed '$d')
assert_test "GET /.well-known/oauth-authorization-server" "200" "$AS_CODE" "$AS_BODY" '.issuer != null'

# ------------------------------------------------------------------------------
# Section 2: StreamableHTTP Transport (/mcp)
# ------------------------------------------------------------------------------
echo -e "\n${BOLD}🌐 2. Testing StreamableHTTP Transport (/mcp)${NC}"

GET_MCP_RESP=$(curl -s -w "\n%{http_code}" "$BASE_URL/mcp")
GET_MCP_CODE=$(echo "$GET_MCP_RESP" | tail -n1)
GET_MCP_BODY=$(echo "$GET_MCP_RESP" | sed '$d')
assert_test "GET /mcp (Should reject with HTTP 405)" "405" "$GET_MCP_CODE" "$GET_MCP_BODY" '.error.code != null'

NO_ACCEPT_RESP=$(curl -s -w "\n%{http_code}" -X POST "$BASE_URL/mcp" \
  -H "Content-Type: application/json" \
  -d '{"jsonrpc":"2.0","id":1,"method":"ping"}')
NO_ACCEPT_CODE=$(echo "$NO_ACCEPT_RESP" | tail -n1)
NO_ACCEPT_BODY=$(echo "$NO_ACCEPT_RESP" | sed '$d')
assert_test "POST /mcp without Accept text/event-stream (HTTP 406)" "406" "$NO_ACCEPT_CODE" "$NO_ACCEPT_BODY"

INIT_PAYLOAD='{
  "jsonrpc": "2.0",
  "id": 1,
  "method": "initialize",
  "params": {
    "protocolVersion": "2024-11-05",
    "capabilities": {},
    "clientInfo": {
      "name": "curl-test-suite",
      "version": "1.0.0"
    }
  }
}'
INIT_RESP=$(curl -s -w "\n%{http_code}" -X POST "$BASE_URL/mcp" \
  -H "Content-Type: application/json" \
  -H "Accept: application/json, text/event-stream" \
  -d "$INIT_PAYLOAD")
INIT_CODE=$(echo "$INIT_RESP" | tail -n1)
INIT_BODY=$(echo "$INIT_RESP" | sed '$d')
assert_test "POST /mcp -> initialize handshake" "200" "$INIT_CODE" "$INIT_BODY" '.result.serverInfo.name != null'

INITIALIZED_NOTIF='{
  "jsonrpc": "2.0",
  "method": "notifications/initialized"
}'
NOTIF_RESP=$(curl -s -w "\n%{http_code}" -X POST "$BASE_URL/mcp" \
  -H "Content-Type: application/json" \
  -H "Accept: application/json, text/event-stream" \
  -d "$INITIALIZED_NOTIF")
NOTIF_CODE=$(echo "$NOTIF_RESP" | tail -n1)
NOTIF_BODY=$(echo "$NOTIF_RESP" | sed '$d')
assert_test "POST /mcp -> notifications/initialized" "200|202" "$NOTIF_CODE" "$NOTIF_BODY"

PING_PAYLOAD='{
  "jsonrpc": "2.0",
  "id": 2,
  "method": "ping"
}'
PING_RESP=$(curl -s -w "\n%{http_code}" -X POST "$BASE_URL/mcp" \
  -H "Content-Type: application/json" \
  -H "Accept: application/json, text/event-stream" \
  -d "$PING_PAYLOAD")
PING_CODE=$(echo "$PING_RESP" | tail -n1)
PING_BODY=$(echo "$PING_RESP" | sed '$d')
assert_test "POST /mcp -> ping" "200" "$PING_CODE" "$PING_BODY" '.result != null'

TOOLS_LIST_PAYLOAD='{
  "jsonrpc": "2.0",
  "id": 3,
  "method": "tools/list",
  "params": {}
}'
LIST_RESP=$(curl -s -w "\n%{http_code}" -X POST "$BASE_URL/mcp" \
  -H "Content-Type: application/json" \
  -H "Accept: application/json, text/event-stream" \
  -d "$TOOLS_LIST_PAYLOAD")
LIST_CODE=$(echo "$LIST_RESP" | tail -n1)
LIST_BODY=$(echo "$LIST_RESP" | sed '$d')
assert_test "POST /mcp -> tools/list" "200" "$LIST_CODE" "$LIST_BODY" '.result.tools != null'

LIST_JSON=$(extract_json "$LIST_BODY")
TOOL_COUNT=$(echo "$LIST_JSON" | jq '.result.tools | length' 2>/dev/null || echo "0")
echo -e "    ${CYAN}ℹ Discovered ${TOOL_COUNT} MCP tools registered${NC}"

AUTH_HEADER=()
EXPECTED_CALL_STATUS="200"
if [ -n "$TOKEN" ]; then
  AUTH_HEADER=(-H "Authorization: Bearer $TOKEN")
else
  EXPECTED_CALL_STATUS="200|401"
fi

SYS_INFO_PAYLOAD='{
  "jsonrpc": "2.0",
  "id": 4,
  "method": "tools/call",
  "params": {
    "name": "get_system_info",
    "arguments": {}
  }
}'
SYS_RESP=$(curl -s -w "\n%{http_code}" -X POST "$BASE_URL/mcp" \
  -H "Content-Type: application/json" \
  -H "Accept: application/json, text/event-stream" \
  "${AUTH_HEADER[@]}" \
  -d "$SYS_INFO_PAYLOAD")
SYS_CODE=$(echo "$SYS_RESP" | tail -n1)
SYS_BODY=$(echo "$SYS_RESP" | sed '$d')
assert_test "POST /mcp -> tools/call (get_system_info)" "$EXPECTED_CALL_STATUS" "$SYS_CODE" "$SYS_BODY"

# ------------------------------------------------------------------------------
# Section 3: Server-Sent Events Transport (/sse & /messages)
# ------------------------------------------------------------------------------
echo -e "\n${BOLD}📡 3. Testing SSE Transport (/sse & /messages)${NC}"

FIFO=$(mktemp -u)
mkfifo "$FIFO"
curl -s -N -H "Accept: text/event-stream" "$BASE_URL/sse" > "$FIFO" &
SSE_PID=$!

SESSION_ID=""
if read -t 3 -r LINE1 < "$FIFO" && read -t 3 -r LINE2 < "$FIFO"; then
  SESSION_ID=$(echo "$LINE1 $LINE2" | grep -o 'sessionId=[^ "]*' | head -n1 | cut -d'=' -f2 | tr -d '\r\n')
fi

if [ -n "$SESSION_ID" ]; then
  assert_test "GET /sse (Session Initialization)" "200" "200" "$LINE1 $LINE2"
  echo -e "    ${CYAN}ℹ Active SSE Session ID: ${SESSION_ID}${NC}"

  SSE_POST_PAYLOAD='{
    "jsonrpc": "2.0",
    "id": 10,
    "method": "ping"
  }'
  MSG_RESP=$(curl -s -w "\n%{http_code}" -X POST "$BASE_URL/messages?sessionId=$SESSION_ID" \
    -H "Content-Type: application/json" \
    "${AUTH_HEADER[@]}" \
    -d "$SSE_POST_PAYLOAD")
  MSG_CODE=$(echo "$MSG_RESP" | tail -n1)
  MSG_BODY=$(echo "$MSG_RESP" | sed '$d')

  assert_test "POST /messages?sessionId=$SESSION_ID" "200|202" "$MSG_CODE" "$MSG_BODY"
else
  TOTAL_TESTS=$((TOTAL_TESTS + 1))
  echo -e "  [Test $TOTAL_TESTS] GET /sse (Session ID Extraction) ... ${RED}FAILED (Could not extract sessionId)${NC}"
  FAILED_TESTS=$((FAILED_TESTS + 1))
fi

kill "$SSE_PID" 2>/dev/null || true
wait "$SSE_PID" 2>/dev/null || true
rm -f "$FIFO"

BAD_MSG_RESP=$(curl -s -w "\n%{http_code}" -X POST "$BASE_URL/messages" \
  -H "Content-Type: application/json" \
  -d '{"jsonrpc":"2.0","id":11,"method":"ping"}')
BAD_MSG_CODE=$(echo "$BAD_MSG_RESP" | tail -n1)
BAD_MSG_BODY=$(echo "$BAD_MSG_RESP" | sed '$d')
assert_test "POST /messages without sessionId (HTTP 400)" "400" "$BAD_MSG_CODE" "$BAD_MSG_BODY"

# ------------------------------------------------------------------------------
# Summary
# ------------------------------------------------------------------------------
echo -e "\n${BOLD}======================================================${NC}"
echo -e "${BOLD}📊 Test Summary${NC}"
echo -e "Total Tests:  $TOTAL_TESTS"
echo -e "Passed:       ${GREEN}$PASSED_TESTS${NC}"
if [ "$FAILED_TESTS" -gt 0 ]; then
  echo -e "Failed:       ${RED}$FAILED_TESTS${NC}"
else
  echo -e "Failed:       ${GREEN}0${NC}"
fi
echo -e "${BOLD}======================================================${NC}\n"

if [ "$FAILED_TESTS" -eq 0 ]; then
  echo -e "${GREEN}${BOLD}🎉 All MCP cURL tests passed successfully!${NC}\n"
  exit 0
else
  echo -e "${RED}${BOLD}❌ Some MCP tests failed.${NC}\n"
  exit 1
fi
