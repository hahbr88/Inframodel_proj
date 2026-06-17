from typing import Protocol
from uuid import uuid4

from fastapi import HTTPException, status

from app.core.config import settings


class AccountProviderPort(Protocol):
    def create_user(self, username: str, password: str) -> str: ...

    def authenticate(self, username: str, password: str) -> None: ...

    def change_password(
        self,
        username: str,
        current_password: str,
        new_password: str,
    ) -> None: ...

    def delete_user(self, username: str) -> None: ...


class LocalAccountProvider:
    def create_user(self, username: str, password: str) -> str:
        return f"local-{uuid4()}"

    def authenticate(self, username: str, password: str) -> None:
        return None

    def change_password(
        self,
        username: str,
        current_password: str,
        new_password: str,
    ) -> None:
        return None

    def delete_user(self, username: str) -> None:
        return None


class CognitoAccountProvider:
    def __init__(self) -> None:
        if not settings.cognito_user_pool_id or not settings.cognito_client_id:
            raise RuntimeError(
                "Cognito settings are required when ACCOUNT_PROVIDER=cognito"
            )
        try:
            import boto3
            from botocore.exceptions import ClientError
        except ImportError as exc:
            raise RuntimeError(
                "boto3 is required when ACCOUNT_PROVIDER=cognito"
            ) from exc

        self._client = boto3.client(
            "cognito-idp",
            region_name=settings.cognito_region,
        )
        self._client_error = ClientError

    def create_user(self, username: str, password: str) -> str:
        try:
            response = self._client.admin_create_user(
                UserPoolId=settings.cognito_user_pool_id,
                Username=username,
                MessageAction="SUPPRESS",
            )
            self._client.admin_set_user_password(
                UserPoolId=settings.cognito_user_pool_id,
                Username=username,
                Password=password,
                Permanent=True,
            )
        except self._client_error as exc:
            self._raise_cognito_error(exc)
        attributes = response["User"].get("Attributes", [])
        sub = next(
            (
                item["Value"]
                for item in attributes
                if item.get("Name") == "sub"
            ),
            username,
        )
        return sub

    def authenticate(self, username: str, password: str) -> None:
        try:
            self._client.admin_initiate_auth(
                UserPoolId=settings.cognito_user_pool_id,
                ClientId=settings.cognito_client_id,
                AuthFlow="ADMIN_USER_PASSWORD_AUTH",
                AuthParameters={
                    "USERNAME": username,
                    "PASSWORD": password,
                },
            )
        except self._client_error as exc:
            self._raise_cognito_error(exc, login=True)

    def change_password(
        self,
        username: str,
        current_password: str,
        new_password: str,
    ) -> None:
        self.authenticate(username, current_password)
        try:
            self._client.admin_set_user_password(
                UserPoolId=settings.cognito_user_pool_id,
                Username=username,
                Password=new_password,
                Permanent=True,
            )
        except self._client_error as exc:
            self._raise_cognito_error(exc)

    def delete_user(self, username: str) -> None:
        try:
            self._client.admin_delete_user(
                UserPoolId=settings.cognito_user_pool_id,
                Username=username,
            )
        except self._client_error as exc:
            self._raise_cognito_error(exc)

    @staticmethod
    def _raise_cognito_error(exc: Exception, login: bool = False) -> None:
        code = getattr(exc, "response", {}).get("Error", {}).get("Code", "")
        if code in {"UsernameExistsException", "AliasExistsException"}:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="Username is already registered",
            ) from exc
        if login or code in {
            "NotAuthorizedException",
            "UserNotFoundException",
            "PasswordResetRequiredException",
        }:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid username or password",
            ) from exc
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail="Cognito account request failed",
        ) from exc


def get_account_provider() -> AccountProviderPort:
    if settings.account_provider == "cognito":
        return CognitoAccountProvider()
    return LocalAccountProvider()
