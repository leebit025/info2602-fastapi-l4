from fastapi import APIRouter, HTTPException, Depends
from sqlmodel import select
from app.database import SessionDep
from app.models import *
from app.auth import encrypt_password, verify_password, create_access_token, AuthDep
from fastapi.security import OAuth2PasswordRequestForm
from typing import Annotated
from fastapi import status

todo_router = APIRouter(tags=["Todo Management"])


def build_todo_response(todo: Todo) -> TodoResponse:
    return TodoResponse(
        id=todo.id,
        text=todo.text,
        done=todo.done,
        categories=[CategoryItem(id=cat.id, text=cat.text) for cat in todo.categories]
    )


@todo_router.get('/todos', response_model=list[TodoResponse])
def get_todos(db: SessionDep, user: AuthDep):
    # Eager load categories to avoid N+1 problem
    todos = db.exec(select(Todo).where(Todo.user_id == user.id)).all()
    return [build_todo_response(todo) for todo in todos]


@todo_router.get('/todo/{id}', response_model=TodoResponse)
def get_todo_by_id(id: int, db: SessionDep, user: AuthDep):
    todo = db.exec(select(Todo).where(Todo.id == id, Todo.user_id == user.id)).one_or_none()
    if not todo:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Unauthorized",
            headers={"WWW-Authenticate": "Bearer"},
        )
    return build_todo_response(todo)


@todo_router.post('/todos', response_model=TodoResponse)
def create_todo(db: SessionDep, user: AuthDep, todo_data: TodoCreate):
    todo = Todo(text=todo_data.text, user_id=user.id)
    try:
        db.add(todo)
        db.commit()
        db.refresh(todo)
        return build_todo_response(todo)
    except Exception:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="An error occurred while creating an item",
        )


@todo_router.put('/todo/{id}', response_model=TodoResponse)
def update_todo(id: int, db: SessionDep, user: AuthDep, todo_data: TodoUpdate):
    todo = db.exec(select(Todo).where(Todo.id == id, Todo.user_id == user.id)).one_or_none()
    if not todo:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Unauthorized",
        )
    if todo_data.text is not None:
        todo.text = todo_data.text
    if todo_data.done is not None:
        todo.done = todo_data.done
    try:
        db.add(todo)
        db.commit()
        db.refresh(todo)
        return build_todo_response(todo)
    except Exception:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="An error occurred while updating an item",
        )


@todo_router.delete('/todo/{id}', status_code=status.HTTP_200_OK)
def delete_todo(id: int, db: SessionDep, user: AuthDep):
    todo = db.exec(select(Todo).where(Todo.id == id, Todo.user_id == user.id)).one_or_none()
    if not todo:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Unauthorized",
        )
    try:
        db.delete(todo)
        db.commit()
        return {"message": "Todo deleted successfully"}
    except Exception:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="An error occurred while deleting an item",
        )