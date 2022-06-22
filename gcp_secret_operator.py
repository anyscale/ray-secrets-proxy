from typing import List, Optional
from ray.util.annotations import PublicAPI
from ray_secret import RaySecret
from ray_secret_operator import  RaySecretOperator

from google.oauth2 import service_account

from google.cloud import secretmanager
from google.api_core.exceptions import ClientError

@PublicAPI
class GCPRaySecretOperator(RaySecretOperator):
    def __init__(self, project_id: str, **kwargs) -> None:
        self.__project_id = project_id
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
        version = "latest" if "version" not in kwargs else kwargs["version"]

        if f"projects/{self.__project_id}/secrets/" not in secret_name:
            secret_name = f"projects/{self.__project_id}/secrets/{secret_name}"

        if "/versions/" not in secret_name:
            secret_name = f"{secret_name}/versions/{version}"

        try:
            response = self.__client.access_secret_version(name=secret_name)

            secret = response.payload.data.decode("UTF-8")
            response.payload.data = None
            return RaySecret(
                secret_name=secret_name,
                secret=secret,
                ttl=ttl,
                metadata=response.payload,
            )
        except ClientError as e:
            raise e

    def list_secrets(self, filter=None) -> List[str]:
        parent = f"projects/{self.__project_id}"

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
