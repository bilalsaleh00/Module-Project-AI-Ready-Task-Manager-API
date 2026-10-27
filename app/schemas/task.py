from typing import Optional

from pydantic import BaseModel, ConfigDict, Field, field_validator


class TaskCreate(BaseModel):
    title: str = Field(
        min_length=1,
        max_length=200
    )

    description: Optional[str] = Field(
        default=None,
        max_length=500
    )

    completed: bool = False


class TaskUpdate(BaseModel):
    title: Optional[str] = Field(
        default=None,
        min_length=1,
        max_length=200
    )

    description: Optional[str] = Field(
        default=None,
        max_length=500
    )

    completed: Optional[bool] = None

    @field_validator("title")
    @classmethod
    def title_must_not_be_null(cls, value):
        if value is None:
            raise ValueError("title must not be null")

        return value

    @field_validator("completed")
    @classmethod
    def completed_must_not_be_null(cls, value):
        if value is None:
            raise ValueError("completed must not be null")

        return value


class TaskResponse(BaseModel):
    id: int
    title: str
    description: Optional[str]
    completed: bool
    owner_id: int

    model_config = ConfigDict(
        from_attributes=True,
        json_schema_extra={
            "example": {
                "id": 1,
                "title": "Finish FastAPI project",
                "description": "Complete Module 5 project",
                "completed": False,
                "owner_id": 1
            }
        }
    )


class TaskSuggestionResponse(BaseModel):
    task_id: int
    task_title: str
    suggestion: str
    source: str
    note: str

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "task_id": 1,
                "task_title": "Finish FastAPI project",
                "suggestion": "Break the task into smaller steps and complete them one at a time.",
                "source": "mock-ai",
                "note": "This is a placeholder suggestion and does not use a real AI model."
            }
        }
    )


class MessageResponse(BaseModel):
    message: str

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "message": "Task 1 deleted"
            }
        }
    )