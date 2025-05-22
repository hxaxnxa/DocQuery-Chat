import os
import weaviate
from weaviate.classes.config import Configure, Property, DataType, VectorDistances
from weaviate.classes.init import Auth, AdditionalConfig, Timeout

def initialize_weaviate():
    try:
        weaviate_url = os.getenv("WEAVIATE_URL")
        weaviate_api_key = os.getenv("WEAVIATE_API_KEY")
        print(f"Connecting to Weaviate Cloud at {weaviate_url}")
        # Initialize Weaviate client for Weaviate Cloud Services
        client = weaviate.connect_to_weaviate_cloud(
            cluster_url=weaviate_url,
            auth_credentials=Auth.api_key(weaviate_api_key),
            additional_config=AdditionalConfig(
                timeout=Timeout(init=30, query=60)  # Increased init timeout
            ),
            skip_init_checks=True  # Skip gRPC health check
        )
        print("Weaviate client initialized successfully")
        if client.is_ready():
            print("Weaviate cluster is ready (REST API)")
        else:
            print("Warning: Weaviate cluster is not ready (REST API)")
        return client
    except Exception as e:
        print(f"Error initializing Weaviate: {e}")
        raise

def create_or_connect_class(client, class_name):
    try:
        print(f"Checking for existing Weaviate class: {class_name}")
        # Check if class exists using collections.exists
        if not client.collections.exists(class_name):
            print(f"Creating new Weaviate class: {class_name}")
            client.collections.create(
                name=class_name,
                properties=[
                    Property(name="content", data_type=DataType.TEXT)
                ],
                vectorizer_config=Configure.Vectorizer.none(),  # Use external embeddings
                vector_index_config=Configure.VectorIndex.hnsw(
                    distance_metric=VectorDistances.COSINE,
                    ef_construction=128,
                    max_connections=32
                )
            )
        collection = client.collections.get(class_name)
        print(f"Connected to Weaviate class: {class_name}")
        return collection
    except Exception as e:
        print(f"Error creating/connecting to Weaviate class: {e}")
        raise