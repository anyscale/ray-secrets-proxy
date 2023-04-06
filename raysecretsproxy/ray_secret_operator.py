from typing import Any, Dict, List, Optional, Tuple
from ray.util.annotations import DeveloperAPI
from .ray_secret import RaySecret


@DeveloperAPI
class RaySecretOperator:
    def __init__(self, **kwargs) -> None:
        raise NotImplementedError

    def initialize(self) -> None:
        """Initializes internal state of the operator."""
        raise NotImplementedError

    def _fetch(self, secret_name: str, **kwargs) -> Tuple[bytes, Dict]:
        """Gets a secret from the underlying provider."""
        raise NotImplementedError

    def get_secret(self, secret_name: str, ttl: Optional[int] = None, **kwargs) -> RaySecret:
        """Gets a RaySecret from the underlying provider.."""
        secret_bytes, metadata = self._fetch(secret_name, **kwargs)
        return RaySecret(
            secret_name=secret_name, secret=secret_bytes, ttl=ttl, metadata=metadata
        )

    def list_secrets(self, filter=Any) -> List[str]:
        """Lists available secret names (not values)."""
        raise NotImplementedError

