#!/bin/bash
# Test script for the respondandrecommend endpoint

curl -X POST 'http://localhost:8000/respondandrecommend' \
  -H 'accept: application/json' \
  -H 'Content-Type: application/json' \
  -d '{
  "query": "most cost friendly estate in nairobi",
  "conversation_id": "test convo06",
  "max_tokens": 1000,
  "temperature": 0.7
}'
