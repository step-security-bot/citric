from __future__ import annotations

import typing as t
from importlib import metadata

import requests

if t.TYPE_CHECKING:
    import sys
    from types import TracebackType

    if sys.version_info >= (3, 11):
        from typing import Self  # noqa: ICN003
    else:
        from typing_extensions import Self


class RESTClient:
    """LimeSurvey REST API client.

    Upon creation, retrieves a session ID that's used for authentication.

    .. warning::
       The REST API is still in early development, so the client is subject to changes.

    Args:
        url: LimeSurvey server URL. For example, ``http://www.yourdomain.com/rest/v1.``.
        username: LimeSurvey user name.
        password: LimeSurvey password.
        requests_session: A :py:class:`requests.Session <requests.Session>` object.

    .. versionadded:: NEXT_VERSION
       Support the REST API.
    """

    USER_AGENT = f"citric/{metadata.version('citric')}"

    def __init__(
        self,
        url: str,
        username: str,
        password: str,
        *,
        requests_session: requests.Session | None = None,
    ) -> None:
        """Create a LimeSurvey REST session."""
        self.url = url
        self._session = requests_session or requests.session()
        self._session.headers["User-Agent"] = self.USER_AGENT

        self.__session_id = self._authenticate(
            username=username,
            password=password,
        )
        self._session.auth = self._auth

    def _authenticate(self, username: str, password: str) -> str:
        """Authenticate with the REST API.

        Args:
            username: LimeSurvey user name.
            password: LimeSurvey password.

        Returns:
            Session ID.
        """
        response = self._session.post(
            url=f"{self.url}/rest/v1/session",
            json={
                "username": username,
                "password": password,
            },
        )
        response.raise_for_status()
        return response.json()

    def close(self) -> None:
        """Delete the session."""
        response = self._session.delete(f"{self.url}/rest/v1/session")
        response.raise_for_status()

    def _auth(self, request: requests.PreparedRequest) -> requests.PreparedRequest:
        """Authenticate with the REST API.

        This is an auth callable for
        :py:attr:`requests.Session.auth <requests.Session.auth>`.

        Args:
            request: Prepared request.

        Returns:
            The prepared request with the ``Authorization`` header set.
        """
        request.headers["Authorization"] = f"Bearer {self.__session_id}"
        return request

    def __enter__(self: Self) -> Self:
        """Context manager for REST session.

        Returns:
            LimeSurvey REST client.
        """
        return self

    def __exit__(
        self,
        exc_type: type[BaseException] | None,
        exc_value: BaseException | None,
        traceback: TracebackType | None,
    ) -> None:
        """Safely exit a REST session.

        Args:
            exc_type: Exception class.
            exc_value: Exception instance.
            traceback: Error traceback.
        """
        self.close()

    def get_surveys(self) -> list[dict[str, t.Any]]:
        """Get all surveys.

        Returns:
            List of surveys.
        """
        response = self._session.get(url=f"{self.url}/rest/v1/survey")
        response.raise_for_status()
        return response.json()["surveys"]

    def get_survey_details(self, survey_id: int) -> dict[str, t.Any]:
        """Get survey details.

        Args:
            survey_id: Survey ID.

        Returns:
            Survey details.
        """
        response = self._session.get(f"{self.url}/rest/v1/survey-detail/{survey_id}")
        response.raise_for_status()
        return response.json()["survey"]

    def update_survey_details(
        self,
        survey_id: int,
        **data: t.Any,
    ) -> bool:
        """Update survey details.

        Args:
            survey_id: Survey ID.
            data: Survey details.

        Returns:
            Updated survey details.
        """
        response = self._session.patch(
            f"{self.url}/rest/v1/survey-detail/{survey_id}",
            json={
                "patch": [
                    {
                        "entity": "survey",
                        "op": "update",
                        "id": survey_id,
                        "props": data,
                    },
                ],
            },
        )
        response.raise_for_status()
        return response.json()
