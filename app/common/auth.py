"""Google API OAuth2 authentication module.

This module provides shared authentication functionality for Google APIs.
"""

import logging
import os
from pathlib import Path
from typing import List

from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow

logger = logging.getLogger(__name__)


class GoogleAuthenticator:
    """Handles OAuth2 authentication for Google APIs."""

    def __init__(self, credentials_file: str, token_file: str, scopes: List[str]):
        """Initialize authenticator.

        Args:
            credentials_file: Path to OAuth2 credentials JSON file
            token_file: Path to token storage file
            scopes: List of OAuth2 scopes to request
        """
        self.credentials_file = credentials_file
        self.token_file = token_file
        self.scopes = scopes

    def authenticate(self) -> Credentials:
        """Authenticate with Google API using OAuth2.

        Returns:
            Authenticated credentials object

        Raises:
            FileNotFoundError: If credentials file doesn't exist
        """
        creds = None

        # Load existing token if available
        if os.path.exists(self.token_file):
            logger.info(f"Loading existing token from {self.token_file}")
            creds = Credentials.from_authorized_user_file(self.token_file, self.scopes)

        # Refresh or create new credentials
        if not creds or not creds.valid:
            if creds and creds.expired and creds.refresh_token:
                logger.info("Refreshing expired token")
                creds.refresh(Request())
            else:
                logger.info("Starting OAuth2 flow for new credentials")
                if not os.path.exists(self.credentials_file):
                    raise FileNotFoundError(
                        f"Credentials file not found: {self.credentials_file}"
                    )

                flow = InstalledAppFlow.from_client_secrets_file(
                    self.credentials_file, self.scopes
                )
                creds = flow.run_local_server(port=0)

            # Save the credentials for future runs
            logger.info(f"Saving token to {self.token_file}")
            Path(self.token_file).parent.mkdir(parents=True, exist_ok=True)
            with open(self.token_file, "w", encoding="utf-8") as token:
                token.write(creds.to_json())

        logger.info("Authentication successful")
        return creds
