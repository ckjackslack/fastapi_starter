gnome-terminal --tab -e '/bin/bash -c "cd client; yarn install; yarn start";bash'
docker build -t fastapi-starter .
docker run -p 8099:8000 fastapi-starter
