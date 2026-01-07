from aiohttp import web
import json
from datetime import datetime
from ...database import (
    create_ad as db_create_ad,
    get_ad as db_get_ad,
    get_all_ads as db_get_all_ads,
    update_ad as db_update_ad,
    delete_ad as db_delete_ad
)


class DateTimeEncoder(json.JSONEncoder):
    def default(self, obj):
        if isinstance(obj, datetime):
            return obj.isoformat()
        return super().default(obj)


def login_required(handler):
    """Decorator to require authentication"""

    async def decorated(request, *args, **kwargs):
        if 'user' not in request:
            raise web.HTTPUnauthorized(reason="Authentication required")
        return await handler(request, *args, **kwargs)

    return decorated


@login_required
async def create_ad_handler(request):
    """Create a new ad"""
    try:
        data = await request.json()
        user = request['user']
        if 'title' not in data:
            raise web.HTTPBadRequest(reason="Title is required")

        ad_data = {
            'title': data['title'],
            'description': data.get('description', ''),
            'owner_id': user['id'],
            'created_at': datetime.utcnow()
        }

        ad_id = await db_create_ad(ad_data)

        return web.json_response(
            {
                'id': ad_id,
                'message': 'Ad created successfully',
                'title': ad_data['title']
            },
            status=201,
            dumps=lambda x: json.dumps(x, cls=DateTimeEncoder)
        )

    except json.JSONDecodeError:
        raise web.HTTPBadRequest(reason="Invalid JSON")
    except Exception as e:
        raise web.HTTPInternalServerError(reason=str(e))


async def get_ad_handler(request):
    """Get ad by ID"""
    try:
        ad_id = int(request.match_info['id'])
        ad = await db_get_ad(ad_id)

        if not ad:
            raise web.HTTPNotFound(reason="Ad not found")

        return web.json_response(
            ad,
            dumps=lambda x: json.dumps(x, cls=DateTimeEncoder)
        )

    except ValueError:
        raise web.HTTPBadRequest(reason="Invalid ad ID")
    except Exception as e:
        raise web.HTTPInternalServerError(reason=str(e))


async def get_ads_handler(request):
    """Get all ads"""
    try:
        ads = await db_get_all_ads()

        return web.json_response(
            ads,
            dumps=lambda x: json.dumps(x, cls=DateTimeEncoder)
        )

    except Exception as e:
        raise web.HTTPInternalServerError(reason=str(e))


@login_required
async def update_ad_handler(request):
    """Update existing ad"""
    try:
        ad_id = int(request.match_info['id'])
        data = await request.json()
        user = request['user']
        ad = await db_get_ad(ad_id)
        if not ad:
            raise web.HTTPNotFound(reason="Ad not found")

        if ad['owner_id'] != user['id']:
            raise web.HTTPForbidden(reason="You can only update your own ads")
        allowed_fields = ['title', 'description']
        update_data = {}

        for field in allowed_fields:
            if field in data:
                update_data[field] = data[field]

        if not update_data:
            raise web.HTTPBadRequest(reason="No fields to update")

        await db_update_ad(ad_id, update_data)

        return web.json_response(
            {'message': 'Ad updated successfully'},
            dumps=lambda x: json.dumps(x, cls=DateTimeEncoder)
        )

    except ValueError:
        raise web.HTTPBadRequest(reason="Invalid ad ID")
    except json.JSONDecodeError:
        raise web.HTTPBadRequest(reason="Invalid JSON")
    except Exception as e:
        raise web.HTTPInternalServerError(reason=str(e))


@login_required
async def delete_ad_handler(request):
    """Delete ad"""
    try:
        ad_id = int(request.match_info['id'])
        user = request['user']
        ad = await db_get_ad(ad_id)
        if not ad:
            raise web.HTTPNotFound(reason="Ad not found")

        if ad['owner_id'] != user['id']:
            raise web.HTTPForbidden(reason="You can only delete your own ads")

        await db_delete_ad(ad_id)

        return web.json_response(
            {'message': 'Ad deleted successfully'},
            dumps=lambda x: json.dumps(x, cls=DateTimeEncoder)
        )

    except ValueError:
        raise web.HTTPBadRequest(reason="Invalid ad ID")
    except Exception as e:
        raise web.HTTPInternalServerError(reason=str(e))