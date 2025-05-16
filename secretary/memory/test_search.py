import sys
from weaviate.classes.query import MetadataQuery

from secretary.memory.db import get_client


def test_search(q: str) -> None:
    client = get_client()

    engram = client.collections.get('Fact')

    response = engram.query.near_text(
        query=q,
        limit=10,
        return_metadata=MetadataQuery(distance=True)
    )

    for o in response.objects:
        print(o.properties)
        print(o.metadata.distance)


if __name__ == "__main__":
    q = sys.argv[1]
    test_search(q)
