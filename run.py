import asyncio
import logging
import signal
from aiohttp import web
import aiohttp_cors

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


async def health_check(request):
    """Health check endpoint"""
    return web.json_response({
        "status": "ok",
        "service": "ads-api"
    })


async def create_app():
    app = web.Application()
    cors = aiohttp_cors.setup(app, defaults={
        "*": aiohttp_cors.ResourceOptions(
            allow_credentials=True,
            expose_headers="*",
            allow_headers="*",
        )
    })

    app.router.add_get('/health', health_check)

    try:
        from app.api.routes import setup_routes
        from app.middlewares import setup_middlewares
        from app.database import init_db, close_db

        setup_middlewares(app)
        setup_routes(app, cors)
        app.on_startup.append(init_db)
        app.on_cleanup.append(close_db)
        logger.info("API routes loaded")
    except ImportError as e:
        logger.warning(f"API routes not available: {e}")

    return app


async def run_app():
    app = await create_app()
    runner = web.AppRunner(app)

    await runner.setup()

    try:
        # Вариант 1: localhost
        site = web.TCPSite(runner, 'localhost', 8080)
        await site.start()
        logger.info("Server started on http://localhost:8080")
    except Exception as e1:
        logger.warning(f"Failed on localhost: {e1}")
        try:
            site = web.TCPSite(runner, '127.0.0.1', 8080)
            await site.start()
            logger.info("Server started on http://127.0.0.1:8080")
        except Exception as e2:
            logger.warning(f"Failed on 127.0.0.1: {e2}")
            try:
                site = web.TCPSite(runner, '0.0.0.0', 8080)
                await site.start()
                logger.info("Server started on http://0.0.0.0:8080")
            except Exception as e3:
                logger.error(f"Failed to start server: {e3}")
                return

    loop = asyncio.get_event_loop()
    stop = asyncio.Event()

    def shutdown():
        logger.info("Shutdown signal received")
        stop.set()

    for sig in (signal.SIGINT, signal.SIGTERM):
        loop.add_signal_handler(sig, shutdown)

    await stop.wait()
    logger.info("Server stopped")
    await runner.cleanup()


if __name__ == "__main__":
    try:
        asyncio.run(run_app())
    except KeyboardInterrupt:
        logger.info("Server stopped by user")
    except Exception as e:
        logger.error(f"Server error: {e}")