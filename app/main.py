from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.database import Base, engine
from app.exceptions import (
    DuplicateError,
    NotFoundError,
    duplicate_handler,
    not_found_handler,
)
from app.models import task, user
from app.routers import auth, tasks


Base.metadata.create_all(bind=engine)


tags_metadata = [
    {
        "name": "Authentication",
        "description": (
            "Register users, log in, and view the current user profile."
        ),
    },
    {
        "name": "Tasks",
        "description": (
            "Create, list, retrieve, update, delete, "
            "and get mock AI suggestions for tasks."
        ),
    },
    {
        "name": "General",
        "description": "General API information and health checks.",
    },
]


app = FastAPI(
    title="AI-Ready Task Manager",
    description="""
A course-level task management API built with FastAPI.

## Features
* User registration and JWT authentication
* Protected task CRUD endpoints
* User task ownership and isolation
* Pydantic validation
* Custom error handling
* Background task notification
* Mock AI suggestion endpoint
* Professional Swagger documentation

## Quick Start
1. Register at `POST /auth/register`
2. Log in at `POST /auth/token`
3. Click **Authorize**
4. Use your Bearer token
5. Create and manage your tasks
""",
    version="1.0.0",
    openapi_tags=tags_metadata,
)


app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:8501",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


app.add_exception_handler(
    NotFoundError,
    not_found_handler,
)

app.add_exception_handler(
    DuplicateError,
    duplicate_handler,
)


app.include_router(
    auth.router,
    prefix="/auth",
    tags=["Authentication"],
)

app.include_router(
    tasks.router,
    prefix="/tasks",
    tags=["Tasks"],
)


@app.get(
    "/",
    tags=["General"],
    summary="API health check",
)
def root():
    """
    Check that the API is running.

    - Returns a simple status message.
    - Does not require authentication.
    """
    return {
        "message": "AI-Ready Task Manager API is running"
    }