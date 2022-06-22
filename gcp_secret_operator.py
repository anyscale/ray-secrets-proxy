from typing import List, Optional
from ray.util.annotations import PublicAPI
from ray_secret import RaySecret
from ray_secret_operator import  RaySecretOperator

from google.oauth2 import service_account

import google.auth
from google.cloud import secretmanager
from google.api_core.exceptions import ClientError

@PublicAPI
class GCPRaySecretOperator(RaySecretOperator):
    def __init__(self, project_name: Optional[str] = None, **kwargs) -> None:
        if project_name is None:
            _, project_name = google.auth.default()
            if project_name is None:
                raise RuntimeError("Could not automatically determine a project ID, please explicitly pass in.")
        self.__project_name = project_name
        self.__credentials = kwargs
        return

    def initialize(self) -> None:
        if "credentials" in self.__credentials:
            creds = service_account.Credentials.from_service_account_info(
                self.__credentials["credentials"]
            )
            self.__client = secretmanager.SecretManagerServiceClient(credentials=creds)
        else:
            self.__client = secretmanager.SecretManagerServiceClient()
        return

    def get_secret(self, secret_name: str, ttl=-1, **kwargs) -> RaySecret:
        version = kwargs.get("version", "latest")

        if not secret_name.startswith("projects/"):
            secret_name = f"projects/{self.__project_name}/secrets/{secret_name}"

        if "/versions/" not in secret_name:
            secret_name = f"{secret_name}/versions/{version}"

        try:
            response = self.__client.access_secret_version(name=secret_name)
            secret = response.payload.data.decode("UTF-8")
            response.payload.data = None
            return RaySecret(
                secret_name=secret_name, secret=secret, ttl=ttl, metadata=response.payload
            )
        except UnicodeDecodeError:
            raise RuntimeError("Secret is not a valid string")
        except ClientError as e:
            raise e

    def list_secrets(self, filter=None) -> List[str]:
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
            raise e
