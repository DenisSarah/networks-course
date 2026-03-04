# REST service

Запуск:

```bash
cd '/home/denis/Рабочий стол/networks-course'
source .venv/bin/activate
cd lab02/rest_service
uvicorn server:app --reload
```

Маршруты:

- `POST /product`
- `GET /product/{id}`
- `PUT /product/{id}`
- `DELETE /product/{id}`
- `GET /products`
- `POST /product/{id}/image`
- `GET /product/{id}/image`

Для загрузки картинки отправляй бинарный файл в тело запроса на `POST /product/{id}/image`.
