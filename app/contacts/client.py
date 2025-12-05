"""Google Contacts API client module."""

import logging
from typing import Any, Dict, List

from googleapiclient.discovery import build

from app.common.auth import GoogleAuthenticator

logger = logging.getLogger(__name__)


class ContactsClient:
    """Client for interacting with Google Contacts (People API)."""

    def __init__(self, credentials_file: str, token_file: str, scopes: List[str]):
        """Initialize Google Contacts client.

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
        """Authenticate with Google People API using OAuth2."""
        authenticator = GoogleAuthenticator(
            self.credentials_file, self.token_file, self.scopes
        )
        creds = authenticator.authenticate()

        # Build the service
        self.service = build("people", "v1", credentials=creds)
        logger.info("Google Contacts API client initialized successfully")

    def get_all_contacts(self) -> List[Dict[str, Any]]:
        """Fetch all contacts with birthday or event information.

        Returns:
            List of contact dictionaries with relevant fields

        Raises:
            Exception: If API request fails
        """
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
