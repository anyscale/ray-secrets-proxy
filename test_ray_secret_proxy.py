from collections import defaultdict
from typing import Any, Dict, List

import ray

from ray_secret_operator import RaySecretOperator
from ray_secret_proxy import RaySecretProxy


ray.init()

class LocalSecretOperator(RaySecretOperator):
    def __init__(self, values: Dict[str, bytes]):
        self.values = defaultdict(bytes)
        self.values.update(values)
        self.initialized = False
        self.num_calls = defaultdict(int)

    def initialize(self) -> None:
        self.initialized = True

    def _fetch(self, name: str, **kwargs):
        assert self.initialized
        self.num_calls[name] += 1
        return self.values[name], self.num_calls

    def list_secrets(self, filter=Any) -> List[str]:
        """Lists available secret names (not values)."""
        return list(self.values.keys())


def test_proxy():
    operator = LocalSecretOperator({})

    proxy = RaySecretProxy.remote(operator, default_ttl=-1)

    assert ray.get(proxy.list_secrets.remote()) == []
    for _ in range(5):
        # Ensure only one call to the underlying operator
        secret = ray.get(proxy.get_secret.remote("abc"))
        assert secret.metadata["abc"] == 1
    secret = ray.get(proxy.get_secret.remote("abc", ttl=0))
    assert secret.metadata["abc"] == 2
    