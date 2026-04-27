# Frontend (React + Redux)

Отдельный фронтенд для backend-проекта книжного магазина.

## Архитектура

Реализована схема из твоей диаграммы:

- `View`: страницы `CatalogPage`, `CartPage`, `AdminPanelPage`, `ProfilePage`
- `Action`: async thunks `fetchBooks`, `createSale`, `getRecommendations`, `loginUser` и др.
- `API service`: единый клиент `src/api/httpClient.js` + endpoint-обёртки
- `Reducer`: `booksReducer`, `cartReducer`, `userReducer`, `salesReducer`, `recommendationsReducer`
- `Store`: `src/app/store.js`

## Подключённые backend endpoint'ы

- `GET /api/books`
- `GET /api/books/search`
- `POST /api/auth/login`
- `GET /api/auth/me`
- `POST /api/auth/logout`
- `POST /api/auth/refresh`
- `POST /api/sales`
- `GET /api/reports/sales`
- `GET /api/recommendations/popular`
- `POST /api/recommendations/cart`
- `GET /api/recommendations/personal`
- `GET /api/clients/me`
- `PUT /api/clients/me`

## Локальный запуск

1. В корне backend запусти Flask-сервер (`http://localhost:5001`).
2. В этой папке:

```bash
cp .env.example .env
npm install
npm run dev
```

Vite проксирует `/api` на backend (`127.0.0.1:5001`), поэтому CORS отдельно не нужен.
