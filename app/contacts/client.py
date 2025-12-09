"""Google Contacts API client module."""

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


class ContactsClient:
    """Client for interacting with Google Contacts (People API)."""

    def __init__(
        self,
        credentials_file: str,
        token_file: str,
        scopes: List[str],
        http_timeout: int = 120,
    ):
        """Initialize Google Contacts client.

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
        """Authenticate with Google People API using OAuth2."""
        authenticator = GoogleAuthenticator(
            self.credentials_file, self.token_file, self.scopes
        )
        creds = authenticator.authenticate()

        # Build the service with timeout configuration
        http = httplib2.Http(timeout=self.http_timeout)
        self.service = build(
            "people",
            "v1",
            credentials=creds,
            http=http,
        )
        logger.info(
            f"Google Contacts API client initialized successfully "
            f"(timeout={self.http_timeout}s)"
        )

    def get_all_contacts(
        self,
        max_attempts: Optional[int] = None,
        min_wait: Optional[int] = None,
        max_wait: Optional[int] = None,
    ) -> List[Dict[str, Any]]:
        """Fetch all contacts with birthday or event information.

        Args:
            max_attempts: Maximum retry attempts (overrides default)
            min_wait: Minimum wait seconds between retries (overrides default)
            max_wait: Maximum wait seconds between retries (overrides default)

        Returns:
            List of contact dictionaries with relevant fields

        Raises:
            Exception: If API request fails after all retries
        """
        # Apply retry decorator dynamically if parameters provided
        if max_attempts or min_wait or max_wait:
            return self._get_all_contacts_with_retry(
                max_attempts or 5,
                min_wait or 4,
                max_wait or 60,
            )
        return self._fetch_contacts()

    def _fetch_contacts(self) -> List[Dict[str, Any]]:
        """Internal method to fetch contacts."""
        logger.info("Fetching contacts from Google People API")

        try:
            results = (
                self.service.people()
                .connections()
                .list(
                    resourceName="people/me",
                    pageSize=1000,
                    personFields="names,nicknames,phoneNumbers,birthdays,events",
                )
                .execute()
            )

            connections = results.get("connections", [])
            logger.info(f"Retrieved {len(connections)} total contacts")

            # Filter contacts that have birthday or event information
            filtered_contacts = [
                conn for conn in connections if self._has_birthday_or_event(conn)
            ]

            logger.info(
                f"Filtered to {len(filtered_contacts)} contacts "
                "with birthdays or events"
            )

            return filtered_contacts

        except Exception as e:
            logger.error(f"Failed to fetch contacts: {e}")
            raise

    def _get_all_contacts_with_retry(
        self, max_attempts: int, min_wait: int, max_wait: int
    ) -> List[Dict[str, Any]]:
        """Fetch contacts with custom retry configuration.

        Args:
            max_attempts: Maximum number of retry attempts
            min_wait: Minimum wait seconds between retries
            max_wait: Maximum wait seconds between retries

        Returns:
            List of contact dictionaries
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
            return self._fetch_contacts()

        return _fetch_with_retry()

    @staticmethod
    def _has_birthday_or_event(contact: Dict[str, Any]) -> bool:
        """Check if contact has birthday or event information.

        Args:
            contact: Contact dictionary from API

        Returns:
            True if contact has birthday or event data
        """
        has_birthday = "birthdays" in contact and contact["birthdays"]
        has_event = "events" in contact and contact["events"]
        return has_birthday or has_event
