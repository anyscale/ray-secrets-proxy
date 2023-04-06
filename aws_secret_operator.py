from typing import Dict, List, Tuple
from ray.util.annotations import PublicAPI
from ray_secret import RaySecret
from ray_secret_operator import  RaySecretOperator

import boto3
from botocore.exceptions import ClientError


@PublicAPI
class AWSRaySecretOperator(RaySecretOperator):
    def __init__(self, **kwargs) -> None:
        self.__credentials = kwargs
        return

    def initialize(self) -> None:
        self.__client = boto3.client("secretsmanager", **self.__credentials)
        return

    def _fetch(self, secret_name: str, **kwargs) -> Tuple[bytes, Dict]:
        try:
            kwargs["SecretId"] = secret_name
            response = self.__client.get_secret_value(**kwargs)
        except ClientError as e:
            if e.response["Error"]["Code"] in ("InvalidParameterException", "InvalidRequestException", "ResourceNotFoundException"):
                raise ValueError(f"Cannot find secret {secret_name} associated arguments: {kwargs}")

            raise e

        # Decrypts secret using the associated KMS key.
        # Depending on whether the secret is a string or binary, one of these fields will be populated.
        if "SecretString" in response:
            secret = response.pop("SecretString").encode()
        else:
            secret = response.pop("SecretBinary")

        secret_name = response.pop("Name")
        response.pop("ResponseMetadata", None)

        return secret, response

    def list_secrets(self, filter=None) -> List[str]:
        # TODO: add pagination
        try:
            if filter is None:
                secret_list = self.__client.list_secrets(MaxResults=100)["SecretList"]
            else:
                secret_list = self.__client.list_secrets(MaxResults=100, Filters=filter)["SecretList"]

            return [secret["Name"] for secret in secret_list]
        except ClientError as e:
            raise e
