from .handlers import ads, auth


def setup_routes(app, cors):
    """Setup all API routes"""

    app.router.add_post('/api/auth/register', auth.register)
    app.router.add_post('/api/auth/login', auth.login)
    app.router.add_post('/api/ads', ads.create_ad_handler)
    app.router.add_get('/api/ads', ads.get_ads_handler)
    app.router.add_get(r'/api/ads/{id:\d+}', ads.get_ad_handler)
    app.router.add_put(r'/api/ads/{id:\d+}', ads.update_ad_handler)
    app.router.add_delete(r'/api/ads/{id:\d+}', ads.delete_ad_handler)

    async def health_check(request):
        return web.json_response({"status": "ok", "service": "ads-api"})

    app.router.add_get('/health', health_check)

    for route in list(app.router.routes()):
        cors.add(route)