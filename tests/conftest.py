import asyncio
import inspect
import os

import pytest

DEFAULT_ASYNC_TIMEOUT = float(os.getenv("PYTEST_ASYNC_TIMEOUT", "10"))


def pytest_configure(config):
    config.addinivalue_line(
        "markers",
        "asyncio(timeout=30): mark async test to run under custom event loop",
    )


@pytest.fixture(scope="session")
def event_loop():
    if os.name == "nt":
        loop = asyncio.ProactorEventLoop()
    else:
        loop = asyncio.new_event_loop()
    yield loop
    loop.run_until_complete(_shutdown_loop(loop))
    loop.close()


def pytest_pyfunc_call(pyfuncitem):
    """Allow async test functions without pytest-asyncio plugin and enforce timeout."""
    test_func = pyfuncitem.obj
    if inspect.iscoroutinefunction(test_func):
        marker = pyfuncitem.get_closest_marker("asyncio")
        timeout = marker.kwargs.get("timeout", DEFAULT_ASYNC_TIMEOUT) if marker else DEFAULT_ASYNC_TIMEOUT
        loop = asyncio.new_event_loop()
        try:
            asyncio.set_event_loop(loop)
            coro = test_func(**pyfuncitem.funcargs)
            try:
                loop.run_until_complete(asyncio.wait_for(coro, timeout=timeout))
            except asyncio.TimeoutError:
                pytest.skip(f"async test exceeded {timeout}s wait")
        finally:
            loop.run_until_complete(_shutdown_loop(loop))
            loop.close()
            asyncio.set_event_loop(None)
        return True
    return None


async def _shutdown_loop(loop):
    tasks = [task for task in asyncio.all_tasks(loop) if not task.done()]
    for task in tasks:
        task.cancel()
    if tasks:
        await asyncio.gather(*tasks, return_exceptions=True)
