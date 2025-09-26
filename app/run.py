import uvicorn

from app.main import *

# -----------------------
# Запуск FastAPI
# -----------------------
if __name__ == '__main__':
    uvicorn.run(app, host=HOST, port=int(PORT))
