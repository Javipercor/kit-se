"""Domain models for the backlog_to_ado tool."""

from dataclasses import dataclass


@dataclass(frozen=True)
class Task:
    """A task that belongs to a user story."""

    title: str
    description: str
    profile: str


@dataclass(frozen=True)
class UserStory:
    """A user story that belongs to a feature."""

    title: str
    description: str
    acceptance_criteria: tuple[str, ...]
    tasks: tuple[Task, ...]


@dataclass(frozen=True)
class Feature:
    """A feature that groups user stories."""

    title: str
    description: str
    user_stories: tuple[UserStory, ...]


@dataclass(frozen=True)
class BacklogModel:
    """Canonical validated backlog model."""

    features: tuple[Feature, ...]
