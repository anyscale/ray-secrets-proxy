from typing import Any, List, Optional
from ray.util.annotations import DeveloperAPI
from ray_secret import RaySecret


@DeveloperAPI
class RaySecretOperator:
    def __init__(self, **kwargs) -> None:
        raise NotImplementedError

    def initialize(self) -> None:
        raise NotImplementedError

    def get_secret(self, secret_name: str, ttl: Optional[int] = None, **kwargs) -> RaySecret:
        raise NotImplementedError

    def list_secrets(self, filter=Any) -> List[str]:
        raise NotImplementedError

