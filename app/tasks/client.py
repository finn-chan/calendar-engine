"""Google Tasks API client."""

import logging
from typing import Any, Dict, List

from googleapiclient.discovery import build

from app.common.auth import GoogleAuthenticator

logger = logging.getLogger(__name__)


class TasksClient:
    """Client for interacting with Google Tasks API."""

    def __init__(self, credentials_file: str, token_file: str, scopes: List[str]):
        """Initialize Google Tasks client.

        Args:
            credentials_file: Path to OAuth2 credentials JSON file
            token_file: Path to token storage file
            scopes: List of OAuth2 scopes to request
        """
        self.credentials_file = credentials_file
        self.token_file = token_file
        self.scopes = scopes
        self.service = None
        self._authenticate()

    def _authenticate(self) -> None:
        """Authenticate with Google Tasks API using OAuth2."""
        authenticator = GoogleAuthenticator(
            self.credentials_file, self.token_file, self.scopes
        )
        creds = authenticator.authenticate()

        # Build the service
        self.service = build("tasks", "v1", credentials=creds)
        logger.info("Successfully authenticated with Google Tasks API")

    def get_task_lists(self) -> List[Dict[str, Any]]:
        """Get all task lists.

        Returns:
            List of task list dictionaries
        """
        logger.info("Fetching task lists")
        results = self.service.tasklists().list().execute()
        task_lists = results.get("items", [])
        logger.info(f"Found {len(task_lists)} task lists")
        return task_lists

    def get_tasks(
        self,
        tasklist_id: str,
        show_completed: bool = True,
        show_hidden: bool = True,
    ) -> List[Dict[str, Any]]:
        """Get all tasks from a task list.

        Args:
            tasklist_id: ID of the task list
            show_completed: Whether to include completed tasks
            show_hidden: Whether to include hidden tasks

        Returns:
            List of task dictionaries
        """
        logger.info(f"Fetching tasks from list {tasklist_id}")

        tasks = []
        page_token = None

        while True:
            results = (
                self.service.tasks()
                .list(
                    tasklist=tasklist_id,
                    showCompleted=show_completed,
                    showHidden=show_hidden,
                    pageToken=page_token,
                )
                .execute()
            )

            items = results.get("items", [])
            tasks.extend(items)

            page_token = results.get("nextPageToken")
            if not page_token:
                break

        logger.info(f"Found {len(tasks)} tasks in list {tasklist_id}")
        return tasks

    def get_all_tasks(
        self, show_completed: bool = True, show_hidden: bool = True
    ) -> Dict[str, Dict[str, Any]]:
        """Get all tasks from all task lists.

        Args:
            show_completed: Whether to include completed tasks
            show_hidden: Whether to include hidden tasks

        Returns:
            Dictionary mapping task list ID to task list info and tasks
        """
        all_tasks = {}
        task_lists = self.get_task_lists()

        for task_list in task_lists:
            list_id = task_list["id"]
            list_title = task_list["title"]

            tasks = self.get_tasks(list_id, show_completed, show_hidden)

            # Store both task list info and tasks
            all_tasks[list_id] = {"title": list_title, "tasks": tasks}

        total_tasks = sum(len(data["tasks"]) for data in all_tasks.values())
        logger.info(f"Total tasks fetched: {total_tasks}")

        return all_tasks
