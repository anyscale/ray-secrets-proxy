from collections import defaultdict
from typing import Any, Dict, List

import pytest
import ray

from raysecretsproxy import AWSRaySecretOperator, GCPRaySecretOperator, RaySecretOperator, RaySecretProxy


@pytest.fixture(scope="session", autouse=True)
def ray_init():
    ray.init(local_mode=True)



def test_proxy():
    class LocalSecretOperator(RaySecretOperator):
        def __init__(self, values: Dict[str, bytes]):
            self.values = values
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

    operator = LocalSecretOperator({
        "abc" : b"abc"
    })

    proxy = RaySecretProxy.remote(operator, default_ttl=-1)

    assert ray.get(proxy.list_secrets.remote()) == ["abc"]
    for _ in range(5):
        # Ensure only one call to the underlying operator
        secret = ray.get(proxy.get_secret.remote("abc"))
        assert secret.metadata["abc"] == 1
    secret = ray.get(proxy.get_secret.remote("abc", ttl=0))
    assert secret.metadata["abc"] == 2
    

@pytest.mark.skip("run manually with credentials automatically discoverable")
@pytest.mark.parametrize(
    "operator",
    [
        pytest.param(GCPRaySecretOperator, id="gcp"),
        pytest.param(AWSRaySecretOperator, id="aws")
    ]
)
def test_actual_operators(operator: RaySecretOperator):
    proxy = RaySecretProxy.remote(operator())
    assert isinstance(ray.get(proxy.list_secrets.remote()), list)
    with pytest.raises(Exception):
        ray.get(proxy.get_secret.remote("not_a_real_secret"))

    assert ray.get(proxy.purge_cache.remote()) is None