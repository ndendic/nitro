import asyncio
import inspect
import threading
from typing import Any, TypeVar, Protocol, Callable
import collections.abc as c
from blinker import ANY, NamedSignal
from nitro.utils import filter_dict, match


F = TypeVar("F", bound=Callable[..., Any])

async def _aiter_sync_gen(gen):
    """Bridge a sync generator to async without blocking the event loop."""
    loop = asyncio.get_running_loop()
    q = asyncio.Queue()
    DONE = object()

    def pump():
        try:
            for item in gen:
                loop.call_soon_threadsafe(q.put_nowait, item)
        finally:
            loop.call_soon_threadsafe(q.put_nowait, DONE)

    threading.Thread(target=pump, daemon=True).start()

    while True:
        item = await q.get()
        if item is DONE:
            break
        yield item

async def _aiter_results(handler, *args, **kwargs):
    """
    Call handler(*args, **kwargs) and yield zero-or-more items:
      - async generator  -> yield each item
      - coroutine        -> yield awaited value once
      - sync generator   -> yield each item (via thread bridge)
      - plain sync value -> yield once
    """
    rv = handler(*args, **kwargs)

    if inspect.isasyncgen(rv):          # async generator
        async for x in rv:
            yield x
        return

    if inspect.isawaitable(rv):         # coroutine/awaitable
        yield await rv
        return

    if inspect.isgenerator(rv):         # sync generator
        async for x in _aiter_sync_gen(rv):
            yield x
        return

    # plain sync value
    yield rv


class Namespace(dict[str, 'Event']):
    """A dict mapping names to events."""

    def event(self, name: str, doc: str | None = None) -> 'Event':
        """Return the :class:`Event` for the given ``name``, creating it
        if required. Repeated calls with the same name return the same event.

        :param name: The name of the event.
        :param doc: The docstring of the event.
        """
        if name not in self:
            self[name] = Event(name, self, doc)

        return self[name]


class _PNamespaceEvent(Protocol):
    def __call__(self, name: str, doc: str | None = None) -> 'Event': ...


default_namespace: Namespace = Namespace()
"""A default :class:`Namespace` for creating named signals. :func:`signal`
creates a :class:`Event` in this namespace.
overides the blinker default_namespace.
"""

event: _PNamespaceEvent = default_namespace.event
"""Return a :class:`Event` in :data:`default_namespace` with the given
``name``, creating it if required. Repeated calls with the same name return the
same signal.
"""

def filter_signals(filter_query: str, namespace: Namespace = default_namespace) -> dict[str, 'Event']:
    return filter_dict(filter_query, namespace)


class Event(NamedSignal):

    def __init__(self, name: str, namespace: Namespace = default_namespace, doc: str | None = None) -> None:
        super().__init__(name, doc)
        # Signal can be in mupltiple namespaces but only one namespace is set as default for filtering connected receivers
        self.namespace: Namespace = namespace
        self.connect_filtered(sender=ANY, weak=False) # connect to all receivers in the namespace

        # Store handler metadata (priority, condition, registration_order)
        self._handler_metadata: dict[Any, dict[str, Any]] = {}
        self._registration_counter: int = 0  # Track registration order for stable sorting

    def connect(self, receiver: F, sender: Any = ANY, weak: bool = True, priority: int = 0, condition: Callable | None = None) -> F:
        """Connect a receiver with optional priority and condition.

        Args:
            receiver: The handler function to connect
            sender: The sender to filter on (default: ANY)
            weak: Whether to use weak references (default: True)
            priority: Handler priority (higher = executes first, default: 0)
            condition: Optional condition function that must return True for handler to execute
        """
        super().connect(receiver, sender, weak)
        self.connect_filtered(sender, weak)

        # Store metadata for this handler including registration order
        self._handler_metadata[id(receiver)] = {
            'priority': priority,
            'condition': condition,
            'receiver': receiver,
            'registration_order': self._registration_counter
        }
        self._registration_counter += 1

        return receiver

    def connect_filtered(self, sender: Any = ANY, weak: bool = True):
        for name, sig in self.namespace.items():
            if match(name, self.name) and name != self.name:
                for r, receiver in sig.receivers.items():
                    self.receivers[r] = receiver
                    self._by_receiver[r].update(sig._by_receiver[r])
                    self._by_sender.update(sig._by_sender)
                    self._by_receiver[sender].add(r)
                    

    def emit(self, sender: Any = ANY, *args, **kwargs):
        """Enhanced emit that handles all handler types with priority, conditions, and cancellation"""
        results = []

        # Get receivers and sort by priority (higher priority first)
        receivers = list(self.receivers_for(sender))
        receivers_with_priority = []
        for receiver in receivers:
            metadata = self._handler_metadata.get(id(receiver), {'priority': 0, 'condition': None, 'registration_order': 0})
            receivers_with_priority.append((receiver, metadata))

        # Sort by priority (descending), then by registration order (ascending) for stable sorting
        receivers_with_priority.sort(key=lambda x: (-x[1]['priority'], x[1]['registration_order']))

        # Execute handlers in priority order
        for receiver, metadata in receivers_with_priority:
            # Check condition if present
            condition = metadata.get('condition')
            if condition is not None:
                try:
                    if not condition(sender, **kwargs):
                        continue  # Skip this handler if condition is False
                except Exception:
                    continue  # Skip on condition error

            # Determine handler type and consume appropriately
            if self._is_async(receiver):
                result = self._schedule_async(receiver, sender, *args, **kwargs)
            else:
                result = self._consume_sync(receiver, sender, *args, **kwargs)

            # Check for cancellation (handler returns False)
            if result is False or (isinstance(result, list) and False in result):
                break  # Stop propagation

            if result is not None:
                results.append(result)

        return results
    
    def _is_async(self, func):
        return asyncio.iscoroutinefunction(func) or inspect.isasyncgenfunction(func)
    
    def _schedule_async(self, receiver, sender, *args, **kwargs):
        """Schedule async handler without blocking"""
        async def consume():
            results = []
            async for item in _aiter_results(receiver, sender, *args, **kwargs):
                if item is not None: results.append(item)
            return results

        try:
            loop = asyncio.get_running_loop()
            loop.create_task(consume())
        except RuntimeError:
            def run_in_thread():
                asyncio.run(consume())
            threading.Thread(target=run_in_thread, daemon=True).start()
            # print(f"No event loop for async handler {receiver.__name__}")
    
    def _consume_sync(self, receiver, sender, **kwargs):
        """Consume sync handler/generator immediately"""
        results = []
        result = receiver(sender, **kwargs)
        if result is not None: results.append(result)
        if inspect.isgenerator(result):
            results = []
            for item in result:
                if item is not None: results.append(item)
        return results
    
    async def emit_async(self, sender: Any = ANY, *args, **kwargs):
        """Fully async emit with parallel execution"""
        tasks = []
        for receiver in self.receivers_for(sender):
            async def consume():
                results = []
                async for item in _aiter_results(receiver, sender, *args, **kwargs):
                    if item is not None: results.append(item)
                return results

            task = asyncio.create_task(consume())
            tasks.append(task)

        # Await all tasks in parallel
        tasks_results = await asyncio.gather(*tasks, return_exceptions=False)

        return [r for r in tasks_results if r is not None]


def on(evt: str|Event, sender: Any = ANY, weak: bool = True, priority: int = 0, condition: Callable | None = None) -> c.Callable[[F], F]:
    """Decorator to connect a handler to an event.

    Args:
        evt: Event name or Event instance
        sender: The sender to filter on (default: ANY)
        weak: Whether to use weak references (default: True)
        priority: Handler priority (higher = executes first, default: 0)
        condition: Optional condition function that must return True for handler to execute
    """
    sigs = filter_signals(evt, default_namespace)
    if not sigs: sigs = {evt: event(evt)}
    def decorator(fn):
        for tpc, sig in sigs.items():
            sig.connect(fn, sender, weak, priority, condition)
        return fn
    return decorator

def emit(event_to_emit: str|Event, sender: Any = ANY, *args, **kwargs):
    event_ = event_to_emit if isinstance(event_to_emit, Event) else event(event_to_emit)
    return event_.emit(sender, *args, **kwargs)

async def emit_async(event_to_emit: str|Event, sender: Any = ANY, *args, **kwargs):
    event_ = event_to_emit if isinstance(event_to_emit, Event) else event(event_to_emit)
    return await event_.emit_async(sender, *args, **kwargs)

# Export all public components
__all__ = [
    'event', 
    'on',
    'emit',
    'emit_async',
    'Event',
    'Namespace',
    'ANY',
    'default_namespace',
]






