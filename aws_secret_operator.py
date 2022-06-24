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
