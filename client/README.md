# client

Small React 19 + Vite front-end for the starter's pizza API (it replaces the original
Create React App + Redux + antd client). It lists pizzas, creates them from the known
toppings, deletes them and starts a "bake" background job, polling its status.

```sh
npm install
npm run dev      # http://localhost:5173, proxies /api to http://127.0.0.1:8000
npm run build    # static files in dist/
```

Point the proxy elsewhere with `API_URL=http://host:port npm run dev`.
