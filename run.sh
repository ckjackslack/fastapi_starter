docker build -t fastapi-starter .
docker run -dp 8099:8000 fastapi-starter
cd client
yarn install
yarn start
