from fastapi import APIRouter, HTTPException, Depends
from sqlmodel import select
from app.database import SessionDep
from app.models import (
    Category, CategoryCreate, CategoryResponse, CategoryItem,
    Todo, TodoResponse, TodoCreate, TodoUpdate, RegularUser
)
from app.auth import AuthDep
from fastapi import status

category_router = APIRouter(tags=["Category Management"])


# Helper function to build TodoResponse with categories
def build_todo_response(todo: Todo) -> TodoResponse:
    return TodoResponse(
        id=todo.id,
        text=todo.text,
        done=todo.done,
        categories=[CategoryItem(id=cat.id, text=cat.text) for cat in todo.categories]
    )


# 1. Create Category - POST /category
@category_router.post('/category', response_model=CategoryResponse, status_code=status.HTTP_201_CREATED)
def create_category(db: SessionDep, user: AuthDep, category_data: CategoryCreate):
    # Create category for current logged in user
    category = Category(text=category_data.text, user_id=user.id)
    try:
        db.add(category)
        db.commit()
        db.refresh(category)
        return CategoryResponse(id=category.id, text=category.text, user_id=category.user_id)
    except Exception:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="An error occurred while creating the category",
        )


# 2. Add Category to Todo - POST /todo/{todo_id}/category/{cat_id}
@category_router.post('/todo/{todo_id}/category/{cat_id}', response_model=TodoResponse)
def add_category_to_todo(todo_id: int, cat_id: int, db: SessionDep, user: AuthDep):
    # Check if todo exists and belongs to user
    todo = db.exec(select(Todo).where(Todo.id == todo_id, Todo.user_id == user.id)).one_or_none()
    if not todo:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Unauthorized to access this todo",
        )
    
    # Check if category exists and belongs to user
    category = db.exec(select(Category).where(Category.id == cat_id, Category.user_id == user.id)).one_or_none()
    if not category:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Unauthorized to access this category",
        )
    
    # Check if category is already assigned
    if category in todo.categories:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Category already assigned to this todo",
        )
    
    # Add category to todo
    todo.categories.append(category)
    try:
        db.add(todo)
        db.commit()
        db.refresh(todo)
        return build_todo_response(todo)
    except Exception:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="An error occurred while adding category to todo",
        )


# 3. Remove Category from Todo - DELETE /todo/{todo_id}/category/{cat_id}
@category_router.delete('/todo/{todo_id}/category/{cat_id}', response_model=TodoResponse)
def remove_category_from_todo(todo_id: int, cat_id: int, db: SessionDep, user: AuthDep):
    # Check if todo exists and belongs to user
    todo = db.exec(select(Todo).where(Todo.id == todo_id, Todo.user_id == user.id)).one_or_none()
    if not todo:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Unauthorized to access this todo",
        )
    
    # Check if category exists and belongs to user
    category = db.exec(select(Category).where(Category.id == cat_id, Category.user_id == user.id)).one_or_none()
    if not category:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Unauthorized to access this category",
        )
    
    # Check if category is actually assigned to this todo
    if category not in todo.categories:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Category is not assigned to this todo",
        )
    
    # Remove category from todo
    todo.categories.remove(category)
    try:
        db.add(todo)
        db.commit()
        db.refresh(todo)
        return build_todo_response(todo)
    except Exception:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="An error occurred while removing category from todo",
        )


# 4. Get todos for category - GET /category/{cat_id}/todos
@category_router.get('/category/{cat_id}/todos', response_model=list[TodoResponse])
def get_todos_for_category(cat_id: int, db: SessionDep, user: AuthDep):
    # Check if category exists and belongs to current logged in user
    category = db.exec(select(Category).where(Category.id == cat_id, Category.user_id == user.id)).one_or_none()
    if not category:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Unauthorized to access this category",
        )
    
    # Return all todos for this category with their categories populated
    return [build_todo_response(todo) for todo in category.todos]