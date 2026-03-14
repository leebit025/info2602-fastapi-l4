import uvicorn
from fastapi import FastAPI
from app.routers.todo import todo_router
from app.routers import main_router
from app.routers.category import category_router

app = FastAPI()
app.include_router(main_router)
app.include_router(todo_router)
app.include_router(category_router)

if __name__ == "__main__":
    uvicorn.run("app.main:app", host="0.0.0.0", port=8000, reload=True)
