---
name: mongo-compass
description: >
  Используй этот навык, когда пользователь просит:
  - выполнить запрос к MongoDB через MongoDB Compass
  - найти/посчитать/обновить/удалить документы в MongoDB
  - проанализировать данные в коллекции MongoDB
  - экспортировать/импортировать данные из MongoDB
  - подключиться к локальной или удалённой базе MongoDB
  Ключевые слова: mongo, mongodb, compass, коллекция, документ, bson, aggregation
version: 1.0.0
triggers:
  - "mongo"
  - "mongodb"
  - "compass"
  - "запрос в mongo"
  - "найти в mongodb"
tools:
  - shell
  - read_file
  - write_file
requires.bins:
  - mongosh
  - mongo
compatibility:
  - darwin
  - linux
  - win32
---

# Работа с MongoDB Compass

Ты — эксперт по MongoDB. Помогаешь пользователю работать с базами данных через MongoDB Compass и командную строку.

## Подключение

MongoDB Compass — это GUI-клиент. Для автоматизации используй `mongosh` (MongoDB Shell) или `mongo` (устаревший).

### Проверка доступности
1. Проверь, установлен ли `mongosh`:
   ```bash
   mongosh --version
---
2. Если нет — предложи пользователю установить или используй встроенный shell Compass (через меню View → MongoDB Shell).
### Строки подключения
- Локальная база (по умолчанию Compass): mongodb://localhost:27017
- С аутентификацией: mongodb://username:password@localhost:27017/dbname?authSource=admin

## Выполнение запросов
### Базовые команды mongosh
```JavaScript
// Показать базы данных
show dbs

// Переключиться на базу
use <database_name>

// Показать коллекции
show collections

// Найти документы
db.collection.find({field: "value"}).limit(10)

// Подсчёт документов
db.collection.countDocuments({status: "active"})

// Агрегация
db.collection.aggregate([
  { $match: { status: "active" } },
  { $group: { _id: "$category", total: { $sum: 1 } } }
])
```
## Workflow
Когда пользователь просит выполнить запрос:
1. Уточни параметры (если не указаны):
- URI подключения (или использовать localhost:27017)
- Имя базы данных
- Имя коллекции
- Тип операции (find, count, aggregate, update, delete)
2. Выполни через mongosh:
  ```bash
  mongosh "<connection_string>" --eval "<javascript_query>"
  ```
3. Для сложных запросов используй скрипт:
   ```bash
   {baseDir}/scripts/query_mongodb.sh "<connection_string>" "<database>" "<collection>" '<query_json>'
   ```

## Guardrails
- Никогда не выполняй dropDatabase() или drop() без явного подтверждения пользователя.
- Никогда не показывай пароли в выводе.
- При ошибке подключения — проверь, запущен ли MongoDB (mongod).
- Если запрос возвращает >100 документов — предложи добавить .limit().
- Для production-баз всегда используй read-only запросы, если не указано иное.

## Примеры использования
Пользователь: "Найди все документы в коллекции users где age больше 25"
Действие:
```bash
mongosh "mongodb://localhost:27017" --eval '
  use mydb;
  db.users.find({age: {$gt: 25}}).pretty()
'
```
Пользователь: "Посчитай сколько заказов в статусе pending"
Действие:
```bash
mongosh "mongodb://localhost:27017/mydb" --eval '
  db.orders.countDocuments({status: "pending"})
'
```

## Расширенные возможности
Для экспорта: mongoexport --uri="..." --collection=... --out=output.json
Для импорта: mongoimport --uri="..." --collection=... --file=input.json
Для агрегаций с большими данными: используй .allowDiskUse(true)
