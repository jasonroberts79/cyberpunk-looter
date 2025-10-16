#!/bin/bash

# Script to test Neo4j Aura Query API connection
# Reference: https://neo4j.com/docs/query-api/current/authentication-authorization/

set -e

# Color codes for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Function to print colored output
print_info() {
    echo -e "${YELLOW}[INFO]${NC} $1"
}

print_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

print_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# Check if required environment variables are set
if [ -z "$NEO4J_URI" ]; then
    print_error "NEO4J_URI environment variable is not set"
    echo "Usage: NEO4J_URI=<uri> NEO4J_USERNAME=<username> NEO4J_PASSWORD=<password> $0"
    exit 1
fi

if [ -z "$NEO4J_USERNAME" ]; then
    print_error "NEO4J_USERNAME environment variable is not set"
    echo "Usage: NEO4J_URI=<uri> NEO4J_USERNAME=<username> NEO4J_PASSWORD=<password> $0"
    exit 1
fi

if [ -z "$NEO4J_PASSWORD" ]; then
    print_error "NEO4J_PASSWORD environment variable is not set"
    echo "Usage: NEO4J_URI=<uri> NEO4J_USERNAME=<username> NEO4J_PASSWORD=<password> $0"
    exit 1
fi

# Mask password for display
MASKED_PASSWORD="${NEO4J_PASSWORD:0:2}$(printf '*%.0s' {1..10})${NEO4J_PASSWORD: -2}"

print_info "Testing Neo4j Aura Query API connection"
print_info "URI: $NEO4J_URI"
print_info "Username: $NEO4J_USERNAME"
print_info "Password: $MASKED_PASSWORD"
echo ""

# Convert neo4j+s:// to https:// for Query API
# Neo4j Aura Query API endpoint format: https://<instance-id>.databases.neo4j.io/db/neo4j/query/v2
QUERY_API_URI=""

if [[ $NEO4J_URI == neo4j+s://* ]]; then
    # Extract the host from neo4j+s:// URI
    HOST=$(echo "$NEO4J_URI" | sed 's|neo4j+s://||' | sed 's|/.*||')
    QUERY_API_URI="https://${HOST}/db/neo4j/query/v2"
    print_info "Converted bolt URI to Query API endpoint: $QUERY_API_URI"
elif [[ $NEO4J_URI == https://* ]]; then
    # Already in HTTPS format, append query endpoint if not present
    if [[ $NEO4J_URI != */query/v2 ]]; then
        QUERY_API_URI="${NEO4J_URI}/db/neo4j/query/v2"
    else
        QUERY_API_URI="$NEO4J_URI"
    fi
    print_info "Using Query API endpoint: $QUERY_API_URI"
else
    print_error "Unsupported URI format. Expected neo4j+s:// or https://"
    exit 1
fi

echo ""

# Create base64 encoded credentials for Basic Auth
CREDENTIALS=$(echo -n "$NEO4J_USERNAME:$NEO4J_PASSWORD" | base64)

# Test query: RETURN 1 as test
QUERY_JSON='{
  "statement": "RETURN 1 as test",
  "parameters": {}
}'

print_info "Sending test query: RETURN 1 as test"
echo ""

# Make the API request
HTTP_CODE=$(curl -s -w "%{http_code}" -o /tmp/neo4j_response.json \
    -X POST \
    -H "Authorization: Basic $CREDENTIALS" \
    -H "Content-Type: application/json" \
    -d "$QUERY_JSON" \
    "$QUERY_API_URI")

echo "HTTP Response Code: $HTTP_CODE"
echo ""

# Check response
if [ "$HTTP_CODE" -eq 200 ]; then
    print_success "Connection successful!"
    echo ""
    print_info "Response body:"
    cat /tmp/neo4j_response.json | jq '.' 2>/dev/null || cat /tmp/neo4j_response.json
    echo ""

    # Try to extract the result
    RESULT=$(cat /tmp/neo4j_response.json | jq -r '.data.values[0][0]' 2>/dev/null || echo "")
    if [ "$RESULT" = "1" ]; then
        print_success "Query executed successfully! Result: $RESULT"
    fi
elif [ "$HTTP_CODE" -eq 401 ]; then
    print_error "Authentication failed (401 Unauthorized)"
    echo ""
    print_info "Response body:"
    cat /tmp/neo4j_response.json
    echo ""
    print_error "Please check your NEO4J_USERNAME and NEO4J_PASSWORD"
    exit 1
elif [ "$HTTP_CODE" -eq 000 ]; then
    print_error "Failed to connect to server"
    echo ""
    print_info "Response:"
    cat /tmp/neo4j_response.json
    echo ""
    print_error "Please check your NEO4J_URI and network connectivity"
    exit 1
else
    print_error "Request failed with HTTP code: $HTTP_CODE"
    echo ""
    print_info "Response body:"
    cat /tmp/neo4j_response.json
    echo ""
    exit 1
fi

# Cleanup
rm -f /tmp/neo4j_response.json

print_success "Neo4j Aura Query API test completed successfully!"
exit 0
