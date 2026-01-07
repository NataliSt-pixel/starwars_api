import asyncio
import logging
import signal
from aiohttp import web
import aiohttp_cors

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


async def create_app():
    app = web.Application()
    cors = aiohttp_cors.setup(app, defaults={
        "*": aiohttp_cors.ResourceOptions(
            allow_credentials=True,
            expose_headers="*",
            allow_headers="*",
        )
    })

    from app.middlewares import setup_middlewares
    from app.api.routes import setup_routes
    from app.database import init_db, close_db
    setup_middlewares(app)
    setup_routes(app, cors)
    app.on_startup.append(lambda app: init_db())
    app.on_cleanup.append(lambda app: close_db())

    return app


async def run_app():
    app = await create_app()
    runner = web.AppRunner(app)

    await runner.setup()
    site = web.TCPSite(runner, '0.0.0.0', 8080)

    logger.info("<Server started on http://0.0.0.0:8080>")
    loop = asyncio.get_event_loop()
    stop = asyncio.Event()

    def shutdown():
        logger.info("<Shutdown signal received>")
        stop.set()

    for sig in (signal.SIGINT, signal.SIGTERM):
        loop.add_signal_handler(sig, shutdown)

    await site.start()
    await stop.wait()
    logger.info("<Server stopped by user>")
    await runner.cleanup()


if __name__ == "__main__":
    try:
        asyncio.run(run_app())
    except KeyboardInterrupt:
        logger.info("<Server stopped by user>")