from NylasIntegration.models.conn import redis_engine


def sync_user_register(user_id: str):
    redis_engine.xadd("calendar_sync_stream", {"user_id": user_id})
    while (
        redis_engine.xread({"calendar_sync_stream": 0})[0][1][-1][1][b"user_id"]
        == user_id
    ):
        pass

    return
