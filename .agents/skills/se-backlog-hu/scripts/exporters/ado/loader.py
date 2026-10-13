"""Load and validate backlog JSON for Azure DevOps export."""

import json
from pathlib import Path
from typing import Any

from .domain import BacklogModel, Feature, Task, UserStory


class BacklogJsonLoader:
    """Load and validate the backlog JSON model."""

    def load(self, json_path: Path) -> BacklogModel:
        """Load a JSON file and return the parsed backlog model."""
        if not json_path.exists():
            raise FileNotFoundError(f"JSON file does not exist: {json_path}")

        raw_text = json_path.read_text(encoding="utf-8")
        payload = json.loads(raw_text)
        return self.load_from_dict(payload)

    def load_from_dict(self, payload: Any) -> BacklogModel:
        """Validate a JSON-compatible object and return the parsed backlog model."""
        if not isinstance(payload, dict):
            raise ValueError("Invalid JSON: root payload must be an object.")

        features_payload = payload.get("features")
        if not isinstance(features_payload, list):
            raise ValueError("Invalid JSON: missing 'features' list.")

        features: list[Feature] = []
        for feature_payload in features_payload:
            if not isinstance(feature_payload, dict):
                raise ValueError("Invalid JSON: each feature must be an object.")

            title = str(feature_payload.get("title", "")).strip()
            description = str(feature_payload.get("description", "")).strip()
            user_stories_payload = feature_payload.get("user_stories")

            if not title or not isinstance(user_stories_payload, list):
                raise ValueError(
                    "Invalid JSON: each feature requires 'title' and 'user_stories'."
                )

            user_stories: list[UserStory] = []
            for story_payload in user_stories_payload:
                user_stories.append(self._load_user_story(story_payload))

            features.append(
                Feature(
                    title=title,
                    description=description,
                    user_stories=tuple(user_stories),
                )
            )

        return BacklogModel(features=tuple(features))

    def _load_user_story(self, payload: Any) -> UserStory:
        if not isinstance(payload, dict):
            raise ValueError("Invalid JSON: each user story must be an object.")

        title = str(payload.get("title", "")).strip()
        description = str(payload.get("description", "")).strip()
        acceptance_criteria_payload = payload.get("acceptance_criteria")
        tasks_payload = payload.get("tasks")

        if (
            not title
            or not isinstance(acceptance_criteria_payload, list)
            or not isinstance(tasks_payload, list)
        ):
            raise ValueError(
                "Invalid JSON: each user story requires 'title', "
                "'acceptance_criteria', and 'tasks'."
            )

        acceptance_criteria = tuple(
            self._normalize_non_empty_string(item, "acceptance criteria item")
            for item in acceptance_criteria_payload
        )
        tasks = tuple(self._load_task(task_payload) for task_payload in tasks_payload)

        return UserStory(
            title=title,
            description=description,
            acceptance_criteria=acceptance_criteria,
            tasks=tasks,
        )

    def _load_task(self, payload: Any) -> Task:
        if not isinstance(payload, dict):
            raise ValueError("Invalid JSON: each task must be an object.")

        title = str(payload.get("title", "")).strip()
        description = str(payload.get("description", "")).strip()
        profile = str(payload.get("profile", "")).strip()

        if not title or not description or not profile:
            raise ValueError(
                "Invalid JSON: each task requires 'title', 'description', and 'profile'."
            )

        return Task(title=title, description=description, profile=profile)

    def _normalize_non_empty_string(self, value: Any, field_name: str) -> str:
        normalized = str(value).strip()
        if not normalized:
            raise ValueError(
                f"Invalid JSON: each {field_name} must be a non-empty string."
            )
        return normalized
