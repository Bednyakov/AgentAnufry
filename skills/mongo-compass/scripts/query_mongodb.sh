#!/bin/bash
# query_mongodb.sh — вспомогательный скрипт для выполнения MongoDB запросов

CONNECTION_STRING="$1"
DATABASE="$2"
COLLECTION="$3"
QUERY="$4"

if [ -z "$CONNECTION_STRING" ] || [ -z "$DATABASE" ] || [ -z "$COLLECTION" ] || [ -z "$QUERY" ]; then
    echo "Usage: $0 <connection_string> <database> <collection> '<query>'"
    echo "Example: $0 'mongodb://localhost:27017' 'mydb' 'users' '{age: {\$gt: 25}}'"
    exit 1
fi

# Формируем и выполняем запрос
mongosh "$CONNECTION_STRING/$DATABASE" --eval "
  const result = db.$COLLECTION.find($QUERY).limit(50).toArray();
  printjson(result);
"
