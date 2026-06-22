import pytest
from fastapi import HTTPException

from app.infrastructure.accounts import CognitoAccountProvider


class FakeClientError(Exception):
    def __init__(self, code: str, message: str) -> None:
        self.response = {
            "Error": {
                "Code": code,
                "Message": message,
            },
        }


class FakeCognitoClient:
    def __init__(self) -> None:
        self.create_kwargs: dict | None = None
        self.password_kwargs: dict | None = None

    def admin_create_user(self, **kwargs):
        self.create_kwargs = kwargs
        return {
            "User": {
                "Attributes": [
                    {"Name": "sub", "Value": "cognito-sub"},
                ],
            },
        }

    def admin_set_user_password(self, **kwargs) -> None:
        self.password_kwargs = kwargs


def test_cognito_create_user_sets_email_attributes_for_email_username() -> None:
    client = FakeCognitoClient()
    provider = CognitoAccountProvider.__new__(CognitoAccountProvider)
    provider._client = client
    provider._client_error = FakeClientError

    sub = provider.create_user("traveler@example.com", "Password123!")

    assert sub == "cognito-sub"
    assert client.create_kwargs is not None
    assert client.create_kwargs["UserAttributes"] == [
        {"Name": "email", "Value": "traveler@example.com"},
        {"Name": "email_verified", "Value": "true"},
    ]
    assert client.password_kwargs is not None
    assert client.password_kwargs["Permanent"] is True


def test_cognito_invalid_password_maps_to_bad_request() -> None:
    error = FakeClientError(
        "InvalidPasswordException",
        "Password must have uppercase characters",
    )

    with pytest.raises(HTTPException) as exc_info:
        CognitoAccountProvider._raise_cognito_error(error)

    assert exc_info.value.status_code == 400
    assert exc_info.value.detail == "Password does not conform to policy"
