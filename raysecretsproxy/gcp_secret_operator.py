from typing import Dict, List, Optional, Tuple
from ray.util.annotations import PublicAPI
from .ray_secret import RaySecret
from .ray_secret_operator import  RaySecretOperator

import google.auth
from google.auth.credentials import Credentials
from google.cloud import secretmanager
from google.api_core.exceptions import ClientError, exception_class_for_http_status

@PublicAPI
class GCPRaySecretOperator(RaySecretOperator):
    def __init__(self, project_name: Optional[str] = None, credentials: Optional[Credentials] = None,  **client_kwargs) -> None:
        if project_name is None:
            _, project_name = google.auth.default()
            if project_name is None:
                raise RuntimeError("Could not automatically determine a project ID, please explicitly pass in.")
        self.__project_name = project_name
        self.__credentials = credentials
        self.__client_kwargs = client_kwargs
        return

    def initialize(self) -> None:
        self.__client = secretmanager.SecretManagerServiceClient(credentials=self.__credentials, **self.__client_kwargs)

    def _fetch(self, secret_name: str, **kwargs) -> Tuple[bytes, Dict]:
        version = kwargs.get("version", "latest")

        if not secret_name.startswith("projects/"):
            secret_name = f"projects/{self.__project_name}/secrets/{secret_name}"

        if "/versions/" not in secret_name:
            secret_name = f"{secret_name}/versions/{version}"

        try:
            response = self.__client.access_secret_version(name=secret_name)
            secret = response.payload.data
            response.payload.data = None
            return secret, response.payload
        except ClientError as e:
            # Create a new error that doesn't have un-picklable objects
            raise exception_class_for_http_status(e.code)(e.message)

    def list_secrets(self, filter=None) -> List[str]:
        # TODO: add pagination
        parent = f"projects/{self.__project_name}"

        try:
            if filter is None:
                secret_list = self.__client.list_secrets(request={"parent": parent})
            else:
                secret_list = self.__client.list_secrets(
                    request={"parent": parent, "filter": filter}
                )

            return [secret.name for secret in secret_list]
        except ClientError as e:
            # Create a new error that doesn't have un-picklable objects
            raise exception_class_for_http_status(e.code)(e.message)
