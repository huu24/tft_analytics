import argparse
import os

from minio import Minio


def main():
    parser = argparse.ArgumentParser(description="Remove old Gold Parquet snapshots from MinIO.")
    parser.add_argument("--retention", type=int, default=2)
    args = parser.parse_args()
    endpoint = os.environ.get("MINIO_ENDPOINT", "http://minio:9000")
    client = Minio(
        endpoint.replace("http://", "").replace("https://", ""),
        access_key=os.environ["MINIO_ACCESS_KEY"],
        secret_key=os.environ["MINIO_SECRET_KEY"],
        secure=endpoint.startswith("https://"),
    )
    bucket = os.environ.get("MINIO_BUCKET", "lakehouse-bucket")
    objects = list(client.list_objects(bucket, prefix="tft-gold/", recursive=True))
    versions = sorted({obj.object_name.split("/", 2)[1] for obj in objects}, reverse=True)
    expired = set(versions[max(args.retention, 1):])
    for obj in objects:
        if obj.object_name.split("/", 2)[1] in expired:
            client.remove_object(bucket, obj.object_name)
    print(f"Removed {len(expired)} expired Gold snapshots; retained {min(len(versions), args.retention)}.")


if __name__ == "__main__":
    main()
