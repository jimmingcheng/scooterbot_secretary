import weaviate
from functools import lru_cache
from weaviate.client import WeaviateClient


@lru_cache(maxsize=1)
def get_client() -> WeaviateClient:
    return weaviate.connect_to_local(host='secretary_vector_db', port=8080, grpc_port=50051)
