"""Export a validated backlog model to Azure DevOps CSV."""

import csv
from dataclasses import dataclass
from pathlib import Path

from .domain import BacklogModel


@dataclass(frozen=True)
class ExportSummary:
    """Useful metadata returned after CSV export."""

    row_count: int
    profile_counts: dict[str, int]


class AdoCsvExporter:
    """Transform a backlog model into Azure DevOps CSV rows."""

    HEADERS = [
        "ID",
        "Work Item Type",
        "Title 1",
        "Title 2",
        "Title 3",
        "Description",
        "Acceptance Criteria",
        "Priority",
        "Tags",
    ]

    def export(self, backlog: BacklogModel, csv_path: Path) -> ExportSummary:
        """Write a CSV file compatible with Azure DevOps Boards imports."""
        rows: list[dict[str, str]] = []
        profile_counts: dict[str, int] = {}

        for feature in backlog.features:
            rows.append(
                {
                    "ID": "",
                    "Work Item Type": "Feature",
                    "Title 1": feature.title,
                    "Title 2": "",
                    "Title 3": "",
                    "Description": feature.description,
                    "Acceptance Criteria": "",
                    "Priority": "2",
                    "Tags": "",
                }
            )

            for story in feature.user_stories:
                criteria = "".join(
                    f"<p>- {criterion}</p>" for criterion in story.acceptance_criteria
                )
                rows.append(
                    {
                        "ID": "",
                        "Work Item Type": "User Story",
                        "Title 1": "",
                        "Title 2": story.title,
                        "Title 3": "",
                        "Description": story.description,
                        "Acceptance Criteria": criteria,
                        "Priority": "2",
                        "Tags": "",
                    }
                )

                for task in story.tasks:
                    profile_counts[task.profile] = (
                        profile_counts.get(task.profile, 0) + 1
                    )
                    rows.append(
                        {
                            "ID": "",
                            "Work Item Type": "Task",
                            "Title 1": "",
                            "Title 2": "",
                            "Title 3": task.title,
                            "Description": task.description,
                            "Acceptance Criteria": "",
                            "Priority": "3",
                            "Tags": task.profile,
                        }
                    )

        with csv_path.open("w", newline="", encoding="utf-8-sig") as csv_file:
            writer = csv.DictWriter(csv_file, fieldnames=self.HEADERS)
            writer.writeheader()
            writer.writerows(rows)

        return ExportSummary(row_count=len(rows), profile_counts=profile_counts)
