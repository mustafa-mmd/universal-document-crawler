from __future__ import annotations

from enum import StrEnum
from typing import Annotated, Literal

from pydantic import BaseModel, Field, HttpUrl, field_validator, model_validator

from config import ALL_SUPPORTED_EXTENSIONS


class JobStatus(StrEnum):
    queued = "queued"
    running = "running"
    paused = "paused"
    completed = "completed"
    failed = "failed"
    stopped = "stopped"


class CrawlJobCreate(BaseModel):
    name: Annotated[str, Field(min_length=2, max_length=100)] = "Untitled crawl"
    url: HttpUrl
    max_depth: Annotated[int, Field(ge=0, le=20)] = 3
    max_pages: Annotated[int, Field(ge=1, le=100_000)] = 500
    max_downloads: Annotated[int, Field(ge=1, le=100_000)] = 500
    same_domain_only: bool = True
    enable_javascript: bool = True
    respect_robots: bool = True
    retry_failed_downloads: bool = True
    concurrent_downloads: Annotated[int, Field(ge=1, le=20)] = 4
    concurrent_crawlers: Annotated[int, Field(ge=1, le=8)] = 1
    timeout_seconds: Annotated[int, Field(ge=5, le=300)] = 30
    rate_limit_seconds: Annotated[float, Field(ge=0, le=30)] = 0.25
    max_retries: Annotated[int, Field(ge=0, le=10)] = 3
    file_types: list[str] = Field(default_factory=lambda: ["pdf", "doc", "docx"])
    include_keywords: list[str] = Field(default_factory=list, max_length=20)
    exclude_keywords: list[str] = Field(default_factory=list, max_length=20)
    filename_contains: str = Field(default="", max_length=120)
    minimum_file_size: int | None = Field(default=None, ge=0)
    maximum_file_size: int | None = Field(default=None, ge=1)
    language: Literal["any", "english", "urdu"] = "any"
    project_id: str | None = Field(default=None, min_length=8, max_length=64)

    @field_validator("name")
    @classmethod
    def validate_name(cls, value: str) -> str:
        value = value.strip()
        if len(value) < 2:
            raise ValueError("Job name must contain at least two visible characters")
        return value

    @field_validator("file_types")
    @classmethod
    def validate_file_types(cls, values: list[str]) -> list[str]:
        normalized = sorted({value.lower().lstrip(".") for value in values})
        allowed = {value.lstrip(".") for value in ALL_SUPPORTED_EXTENSIONS}
        invalid = set(normalized) - allowed
        if invalid:
            raise ValueError(f"Unsupported file types: {', '.join(sorted(invalid))}")
        if not normalized:
            raise ValueError("Select at least one file type")
        return normalized

    @model_validator(mode="after")
    def validate_sizes(self) -> "CrawlJobCreate":
        if (
            self.minimum_file_size is not None
            and self.maximum_file_size is not None
            and self.minimum_file_size > self.maximum_file_size
        ):
            raise ValueError("minimum_file_size cannot exceed maximum_file_size")
        return self


class JobActionRequest(BaseModel):
    action: Literal["start", "pause", "resume", "stop", "restart", "duplicate"]


class SettingsUpdate(BaseModel):
    download_directory: str | None = Field(default=None, max_length=500)
    concurrent_downloads: int | None = Field(default=None, ge=1, le=20)
    concurrent_crawlers: int | None = Field(default=None, ge=1, le=8)
    browser_type: Literal["chromium", "firefox", "webkit"] | None = None
    headless: bool | None = None
    user_agent: str | None = Field(default=None, max_length=500)
    proxy: str | None = Field(default=None, max_length=500)
    timeout_seconds: int | None = Field(default=None, ge=5, le=300)
    retry_count: int | None = Field(default=None, ge=0, le=10)
    language_preference: Literal["any", "english", "urdu"] | None = None


class ProjectCreate(BaseModel):
    name: Annotated[str, Field(min_length=2, max_length=100)]
    description: str = Field(default="", max_length=500)
    color: str = Field(default="#3b82f6", pattern=r"^#[0-9a-fA-F]{6}$")

    @field_validator("name")
    @classmethod
    def validate_name(cls, value: str) -> str:
        value = value.strip()
        if len(value) < 2:
            raise ValueError("Project name must contain at least two visible characters")
        return value


class ProjectUpdate(BaseModel):
    name: Annotated[str | None, Field(min_length=2, max_length=100)] = None
    description: str | None = Field(default=None, max_length=500)
    color: str | None = Field(default=None, pattern=r"^#[0-9a-fA-F]{6}$")

    @field_validator("name")
    @classmethod
    def validate_name(cls, value: str | None) -> str | None:
        if value is None:
            return None
        value = value.strip()
        if len(value) < 2:
            raise ValueError("Project name must contain at least two visible characters")
        return value


class DocumentRename(BaseModel):
    name: Annotated[str, Field(min_length=1, max_length=180)]
