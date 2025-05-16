from weaviate.classes.config import Configure
from weaviate.classes.config import DataType
from weaviate.classes.config import Property
from weaviate.client import WeaviateClient

from secretary.memory.db import get_client


def delete_collections(client: WeaviateClient) -> None:
    client.collections.delete('Fact')
    client.collections.delete('Engram')


def create_fact_collection(client: WeaviateClient) -> None:
    client.collections.create(
        'Fact',
        properties=[
            Property(name='userId', data_type=DataType.TEXT),
            Property(name='content', data_type=DataType.TEXT),
            Property(name='timestamp', data_type=DataType.INT),
            Property(name='tags', data_type=DataType.TEXT_ARRAY),
        ],
        vectorizer_config=[
            Configure.NamedVectors.text2vec_openai(
                name="text_embeddings",
                source_properties=["summary", "description"],
                model="text-embedding-3-large",
                dimensions=1024
            )
        ],
    )


def create_engram_collection(client: WeaviateClient) -> None:
    client.collections.create(
        'Engram',
        properties=[
            Property(name='userId', data_type=DataType.TEXT),
            Property(name='content', data_type=DataType.TEXT),
            Property(name='summary', data_type=DataType.TEXT),
            Property(name='startTimestamp', data_type=DataType.INT),
            Property(name='endTimestamp', data_type=DataType.INT),
            Property(name='tags', data_type=DataType.TEXT_ARRAY),
        ],
        vectorizer_config=[
            Configure.NamedVectors.text2vec_openai(
                name="text_embeddings",
                source_properties=["summary", "description"],
                model="text-embedding-3-large",
                dimensions=1024
            )
        ],
    )


def run() -> None:
    client = get_client()

    delete_collections(client)

    create_fact_collection(client)
    create_engram_collection(client)

    client.close()


if __name__ == "__main__":
    run()
