#!/bin/bash

# TokenWise API Examples using curl

BASE_URL="http://localhost:8000"

echo "🎯 TokenWise API Examples"
echo "========================="
echo ""

# Example 1: Health Check
echo "1️⃣  Health Check"
echo "   curl $BASE_URL/health"
echo ""
curl -s $BASE_URL/health | python3 -m json.tool
echo ""
echo "---"
echo ""

# Example 2: Basic Optimization
echo "2️⃣  Basic Context Optimization"
echo ""
curl -s -X POST $BASE_URL/optimize \
  -H "Content-Type: application/json" \
  -d '{
    "query": "How do I add two numbers?",
    "context": [
      {
        "id": "math_utils",
        "text": "def add(a, b): return a + b\n\ndef subtract(a, b): return a - b\n\ndef multiply(a, b): return a * b",
        "type": "code"
      }
    ],
    "targetTokens": 100
  }' | python3 -m json.tool

echo ""
echo "---"
echo ""

# Example 3: Optimization with Strategy
echo "3️⃣  Optimization with Diversity Strategy"
echo ""
curl -s -X POST $BASE_URL/optimize \
  -H "Content-Type: application/json" \
  -d '{
    "query": "Authentication and database functions",
    "context": [
      {
        "id": "auth",
        "text": "def login(user, pass): # authenticate user\n    return jwt_token",
        "type": "code"
      },
      {
        "id": "db",
        "text": "def get_user(id): # fetch from database\n    return user",
        "type": "code"
      }
    ],
    "targetTokens": 200,
    "options": {
      "strategy": "diversity",
      "diversityLambda": 0.5
    }
  }' | python3 -m json.tool

echo ""
echo "---"
echo ""

# Example 4: Get Statistics
echo "4️⃣  System Statistics"
echo "   curl $BASE_URL/stats"
echo ""
curl -s $BASE_URL/stats | python3 -m json.tool
echo ""
echo "---"
echo ""

# Example 5: Index Content
echo "5️⃣  Index Content in Vector Store"
echo ""
curl -s -X POST $BASE_URL/index \
  -H "Content-Type: application/json" \
  -d '{
    "id": "tutorial_doc",
    "text": "This is a comprehensive tutorial on using the API. It covers authentication, data fetching, and error handling.",
    "type": "docs"
  }' | python3 -m json.tool

echo ""
echo "========================="
echo "✅ Examples complete!"

