"""Load and validate the backlog input model from JSON."""

import json
from pathlib import Path
from typing import Any

from ..models import Activity, Block, InputModel, UserStory


class InputJsonLoader:
    """Load and validate the model from a JSON file."""

    DEFAULT_PHASE = "Unassigned"

    def load(self, json_path: Path) -> InputModel:
        """Load a JSON file and return the parsed input model."""
        if not json_path.exists():
            raise FileNotFoundError(f"JSON file does not exist: {json_path}")

        raw_text: str = json_path.read_text(encoding="utf-8")
        payload: dict[str, Any] = json.loads(raw_text)

        user_stories_payload = payload.get("userStories")
        if not isinstance(user_stories_payload, list):
            raise ValueError("Invalid JSON: missing 'userStories' list.")

        user_stories: list[UserStory] = []
        for us in user_stories_payload:
            phase = self._normalize_phase(us.get("phase"))
            title = str(us.get("title", "")).strip()
            blocks_payload = us.get("blocks")

            if not title or not isinstance(blocks_payload, list):
                raise ValueError(
                    "Invalid JSON: each userStory requires 'title' and 'blocks'."
                )

            blocks: list[Block] = []
            for b in blocks_payload:
                block_name = str(b.get("name", "")).strip()
                activities_payload = b.get("activities")
                if not block_name or not isinstance(activities_payload, list):
                    raise ValueError(
                        "Invalid JSON: each block requires 'name' and 'activities'."
                    )

                activities: list[Activity] = []
                for a in activities_payload:
                    raw_hours = a.get("hours", 0)
                    hours_value = (
                        raw_hours if isinstance(raw_hours, str) else float(raw_hours)
                    )

                    activity = Activity(
                        name=str(a.get("name", "")).strip(),
                        activity_type=str(a.get("activityType", "")).strip(),
                        role=str(a.get("role", "")).strip(),
                        level=str(a.get("level", "")).strip(),
                        hours=hours_value,
                        risk=int(a.get("risk", 0)),
                    )
                    if not activity.name:
                        raise ValueError("Invalid JSON: each activity requires 'name'.")
                    activities.append(activity)

                blocks.append(Block(name=block_name, activities=tuple(activities)))

            user_stories.append(
                UserStory(phase=phase, title=title, blocks=tuple(blocks))
            )

        return InputModel(user_stories=tuple(user_stories))

    def _normalize_phase(self, raw_phase: Any) -> str:
        phase = str(raw_phase or "").strip()
        if phase:
            return phase
        return self.DEFAULT_PHASE
