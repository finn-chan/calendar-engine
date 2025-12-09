"""Google Tasks API client."""

import logging
from typing import Any, Dict, List, Optional

import httplib2
from googleapiclient.discovery import build
from tenacity import (
    retry,
    retry_if_exception_type,
    stop_after_attempt,
    wait_exponential,
)

from app.common.auth import GoogleAuthenticator

logger = logging.getLogger(__name__)


class TasksClient:
    """Client for interacting with Google Tasks API."""

    def __init__(
        self,
        credentials_file: str,
        token_file: str,
        scopes: List[str],
        http_timeout: int = 120,
    ):
        """Initialize Google Tasks client.

        Args:
            credentials_file: Path to OAuth2 credentials JSON file
            token_file: Path to token storage file
            scopes: List of OAuth2 scopes to request
            http_timeout: HTTP request timeout in seconds
        """
        self.credentials_file = credentials_file
        self.token_file = token_file
        self.scopes = scopes
        self.http_timeout = http_timeout
        self.service = None
        self._authenticate()

    def _authenticate(self) -> None:
        """Authenticate with Google Tasks API using OAuth2."""
        authenticator = GoogleAuthenticator(
            self.credentials_file, self.token_file, self.scopes
        )
        creds = authenticator.authenticate()

        # Build the service with timeout configuration
        http = httplib2.Http(timeout=self.http_timeout)
        self.service = build(
            "tasks",
            "v1",
            credentials=creds,
            http=http,
        )
        logger.info(
            f"Successfully authenticated with Google Tasks API "
            f"(timeout={self.http_timeout}s)"
        )

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
        self,
        show_completed: bool = True,
        show_hidden: bool = True,
        max_attempts: Optional[int] = None,
        min_wait: Optional[int] = None,
        max_wait: Optional[int] = None,
    ) -> Dict[str, Dict[str, Any]]:
        """Get all tasks from all task lists.

        Args:
            show_completed: Whether to include completed tasks
            show_hidden: Whether to include hidden tasks
            max_attempts: Maximum retry attempts (overrides default)
            min_wait: Minimum wait seconds between retries (overrides default)
            max_wait: Maximum wait seconds between retries (overrides default)

        Returns:
            Dictionary mapping task list ID to task list info and tasks
        """
        # Apply retry decorator dynamically if parameters provided
        if max_attempts or min_wait or max_wait:
            return self._get_all_tasks_with_retry(
                show_completed,
                show_hidden,
                max_attempts or 5,
                min_wait or 4,
                max_wait or 60,
            )
        return self._fetch_all_tasks(show_completed, show_hidden)

    def _fetch_all_tasks(
        self, show_completed: bool, show_hidden: bool
    ) -> Dict[str, Dict[str, Any]]:
        """Internal method to fetch all tasks."""
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

    def _get_all_tasks_with_retry(
        self,
        show_completed: bool,
        show_hidden: bool,
        max_attempts: int,
        min_wait: int,
        max_wait: int,
    ) -> Dict[str, Dict[str, Any]]:
        """Fetch tasks with custom retry configuration.

        Args:
            show_completed: Whether to include completed tasks
            show_hidden: Whether to include hidden tasks
            max_attempts: Maximum number of retry attempts
            min_wait: Minimum wait seconds between retries
            max_wait: Maximum wait seconds between retries

        Returns:
            Dictionary mapping task list ID to task list info and tasks
        """
        logger.info(
            f"Using custom retry config: max_attempts={max_attempts}, "
            f"min_wait={min_wait}s, max_wait={max_wait}s"
        )

        @retry(
            retry=retry_if_exception_type(Exception),
            stop=stop_after_attempt(max_attempts),
            wait=wait_exponential(multiplier=1, min=min_wait, max=max_wait),
            reraise=True,
            before_sleep=lambda retry_state: logger.warning(
                f"Retry attempt {retry_state.attempt_number}/{max_attempts} "
                f"after error: {retry_state.outcome.exception()}"
            ),
        )
        def _fetch_with_retry():
            return self._fetch_all_tasks(show_completed, show_hidden)

        return _fetch_with_retry()
