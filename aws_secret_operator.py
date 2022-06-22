from typing import List
from ray.util.annotations import PublicAPI
from ray_secret import RaySecret
from ray_secret_operator import  RaySecretOperator

import boto3
import base64
from botocore.exceptions import ClientError


@PublicAPI
class AWSRaySecretOperator(RaySecretOperator):
    def __init__(self, **kwargs) -> None:
        self.__credentials = kwargs
        return

    def initialize(self) -> None:
        self.__client = boto3.client("secretsmanager", **self.__credentials)
        return

    def get_secret(self, secret_name: str, ttl=-1, **kwargs) -> RaySecret:
        try:
            kwargs["SecretId"] = secret_name
            response = self.__client.get_secret_value(**kwargs)
        except ClientError as e:
            if e.response["Error"]["Code"] == "DecryptionFailureException":
                # Secrets Manager can't decrypt the protected secret text using the provided KMS key.
                # Deal with the exception here, and/or rethrow at your discretion.
                raise e
            elif e.response["Error"]["Code"] == "InternalServiceErrorException":
                # An error occurred on the server side.
                # Deal with the exception here, and/or rethrow at your discretion.
                raise e
            elif e.response["Error"]["Code"] == "InvalidParameterException":
                # You provided an invalid value for a parameter.
                # Deal with the exception here, and/or rethrow at your discretion.
                raise e
            elif e.response["Error"]["Code"] == "InvalidRequestException":
                # You provided a parameter value that is not valid for the current state of the resource.
                # Deal with the exception here, and/or rethrow at your discretion.
                raise e
            elif e.response["Error"]["Code"] == "ResourceNotFoundException":
                # We can't find the resource that you asked for.
                # Deal with the exception here, and/or rethrow at your discretion.
                raise e
            else:
                raise e
        else:
            # Decrypts secret using the associated KMS key.
            # Depending on whether the secret is a string or binary, one of these fields will be populated.
            if "SecretString" in response:
                secret = response.pop("SecretString")
            else:
                secret = base64.b64decode(response.pop("SecretBinary"))

            secret_name = response.pop("Name")
            response.pop("ResponseMetadata", None)

            return RaySecret(
                secret_name=secret_name, secret=secret, ttl=ttl, metadata=response
            )

    def list_secrets(self, filter=None) -> List[str]:
        try:
            if filter is None:
                secret_list = self.__client.list_secrets()["SecretList"]
            else:
                secret_list = self.__client.list_secrets(Filters=filter)["SecretList"]

            return [secret["Name"] for secret in secret_list]
        except ClientError as e:
            raise e
