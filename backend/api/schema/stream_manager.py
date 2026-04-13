import asyncio

class StreamManager:
    def __init__(self):
        self.queues = {}

    def get_queue(self, thread_id: str):
        if thread_id not in self.queues:
            self.queues[thread_id] = asyncio.Queue()
        return self.queues[thread_id]

    async def publish(self, thread_id: str, data: dict):
        queue = self.get_queue(thread_id)
        await queue.put(data)

    async def close(self, thread_id: str):
        queue = self.get_queue(thread_id)
        await queue.put({"event": "stream_end"})
