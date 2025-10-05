import datetime as dt

from pydantic import BaseModel, Field


class WorkoutIn(BaseModel):
    title: str = Field(min_length=1, max_length=100)
    date: dt.date = Field(default_factory=dt.date.today)
    notes: str | None = None
    duration_min: int | None = Field(default=None, ge=1, le=1440)


class WorkoutOut(WorkoutIn):
    id: int


class WorkoutUpdate(BaseModel):
    title: str | None = Field(default=None, min_length=1, max_length=100)
    date: dt.date | None = None
    notes: str | None = None
    duration_min: int | None = Field(default=None, ge=1, le=1440)
