import asyncio


class StreamManager:
    """Manage per-thread asyncio queues for server-sent events.

    The manager stores one queue per workflow thread so background agent tasks
    can publish events while the SSE endpoint consumes them independently.
    """

    def __init__(self):
        """Initialize the queue registry used for active stream threads.

        Args:
            None: The queue registry starts empty.

        Returns:
            None: The constructor only prepares internal state.
        """
        self.queues = {}

    def get_queue(self, thread_id: str):
        """Return the queue associated with a workflow thread.

        Args:
            thread_id: Unique thread identifier for the blog run.

        Returns:
            asyncio.Queue: Existing queue for the thread or a newly created one.
        """
        if thread_id not in self.queues:
            self.queues[thread_id] = asyncio.Queue()
        return self.queues[thread_id]

    async def publish(self, thread_id: str, data: dict):
        """Publish an event payload to a thread-specific queue.

        Args:
            thread_id: Unique thread identifier for the blog run.
            data: JSON-serializable event payload to enqueue.

        Returns:
            None: The event is pushed to the queue asynchronously.
        """
        queue = self.get_queue(thread_id)
        await queue.put(data)

    async def close(self, thread_id: str):
        """Signal that a stream has finished by enqueueing the terminal event.

        Args:
            thread_id: Unique thread identifier for the blog run.

        Returns:
            None: The terminal stream_end event is enqueued for consumers.
        """
        queue = self.get_queue(thread_id)
        await queue.put({"event": "stream_end"})
