from fastapi import APIRouter, BackgroundTasks, Depends
from sqlalchemy.orm import Session

from app.auth import get_current_user
from app.database import get_db
from app.exceptions import DuplicateError, NotFoundError
from app.models.task import Task
from app.models.user import User
from app.schemas.task import (
    MessageResponse,
    TaskCreate,
    TaskResponse,
    TaskSuggestionResponse,
    TaskUpdate,
)


router = APIRouter()


def get_owned_task_or_404(
    db: Session,
    task_id: int,
    user_id: int,
) -> Task:
    task = db.query(Task).filter(
        Task.id == task_id,
        Task.owner_id == user_id,
    ).first()

    if task is None:
        raise NotFoundError(
            f"Task {task_id} not found"
        )

    return task


def notify_task_created(
    task_id: int,
    title: str,
) -> None:
    print(
        f"Task {task_id} created: {title}"
    )


@router.post(
    "/",
    response_model=TaskResponse,
    status_code=201,
    summary="Create a new task",
    responses={
        409: {
            "description": "Duplicate task title"
        },
        422: {
            "description": "Validation error"
        },
    },
)
def create_task(
    task: TaskCreate,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Create a task for the authenticated user.

    - **title**: Required, 1-200 characters.
    - **description**: Optional, up to 500 characters.
    - **completed**: Defaults to `false`.
    """
    existing = db.query(Task).filter(
        Task.owner_id == current_user.id,
        Task.title == task.title,
    ).first()

    if existing:
        raise DuplicateError(
            "A task with this title already exists"
        )

    db_task = Task(
        **task.model_dump(),
        owner_id=current_user.id,
    )

    db.add(db_task)
    db.commit()
    db.refresh(db_task)

    background_tasks.add_task(
        notify_task_created,
        db_task.id,
        db_task.title,
    )

    return db_task


@router.get(
    "/",
    response_model=list[TaskResponse],
    summary="List my tasks",
)
def list_tasks(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Return only the authenticated user's tasks.

    - Other users' tasks are not included.
    - Requires authentication.
    """
    return db.query(Task).filter(
        Task.owner_id == current_user.id
    ).all()


@router.get(
    "/{task_id}",
    response_model=TaskResponse,
    summary="Get one owned task",
    responses={
        404: {
            "description": "Task not found"
        }
    },
)
def get_task(
    task_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Get one task owned by the current user.

    - Returns `404` if the task does not exist.
    - Also returns `404` if the task belongs to another user.
    """
    return get_owned_task_or_404(
        db,
        task_id,
        current_user.id,
    )


@router.patch(
    "/{task_id}",
    response_model=TaskResponse,
    summary="Update an owned task",
    responses={
        404: {
            "description": "Task not found"
        },
        409: {
            "description": "Duplicate task title"
        },
        422: {
            "description": "Validation error"
        },
    },
)
def update_task(
    task_id: int,
    task_update: TaskUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Partially update an owned task.

    - Only explicitly supplied fields are changed.
    - **description** may be `null`.
    - **title** and **completed** may not be `null`.
    """
    db_task = get_owned_task_or_404(
        db,
        task_id,
        current_user.id,
    )

    update_data = task_update.model_dump(
        exclude_unset=True
    )

    if "title" in update_data:
        duplicate = db.query(Task).filter(
            Task.owner_id == current_user.id,
            Task.title == update_data["title"],
            Task.id != task_id,
        ).first()

        if duplicate:
            raise DuplicateError(
                "A task with this title already exists"
            )

    for field, value in update_data.items():
        setattr(
            db_task,
            field,
            value,
        )

    db.commit()
    db.refresh(db_task)

    return db_task


@router.delete(
    "/{task_id}",
    response_model=MessageResponse,
    summary="Delete an owned task",
    responses={
        404: {
            "description": "Task not found"
        }
    },
)
def delete_task(
    task_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Delete a task owned by the current user.

    - Returns `404` for missing tasks.
    - Returns `404` for another user's task.
    """
    db_task = get_owned_task_or_404(
        db,
        task_id,
        current_user.id,
    )

    db.delete(db_task)
    db.commit()

    return {
        "message": f"Task {task_id} deleted"
    }


@router.get(
    "/{task_id}/suggest",
    response_model=TaskSuggestionResponse,
    summary="Get a mock AI suggestion",
    responses={
        404: {
            "description": "Task not found"
        }
    },
)
def suggest_for_task(
    task_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Return a fixed placeholder suggestion for an owned task.

    - No real AI model is called.
    - The task must belong to the authenticated user.
    """
    task = get_owned_task_or_404(
        db,
        task_id,
        current_user.id,
    )

    return {
        "task_id": task.id,
        "task_title": task.title,
        "suggestion": (
            "Break the task into smaller steps "
            "and complete them one at a time."
        ),
        "source": "mock-ai",
        "note": (
            "This is a placeholder suggestion "
            "and does not use a real AI model."
        ),
    }