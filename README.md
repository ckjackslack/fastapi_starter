# fastapi_starter
# Basic FastAPI starter including:
- Uvicorn async server (+)
- Pydantic (+)
- TortoiseORM (todo)
- OAuth2 + JWT (todo)
- aiohttp (todo)
- simple REST / CRUD api (partially finished: GET, POST, DELETE available)

#### If you have Linux, there is a bash script which will pull the image, build the container and run the app:
```sh
./run.sh
```

#### You can access following web routes:
- http://localhost:8099/pizzas (basic GET request returning some dummy content as JSON)
- http://localhost:8099/docs (Swagger interactive documentation where one can test the routes)

#### Project directory structure:
```console
$ tree
.
├── Dockerfile
├── Pipfile
├── Pipfile.lock
├── README.md
├── requirements.txt
├── run.sh
└── src
    ├── main.py
    ├── models.py
    └── schemas.py

1 directory, 9 files
```