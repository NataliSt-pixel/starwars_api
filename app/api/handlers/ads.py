from aiohttp import web
import json
from datetime import datetime
from ...database import create_ad, get_ad, get_all_ads, update_ad, delete_ad
from ...validators import validate_ad_creation, validate_ad_update


class DateTimeEncoder(json.JSONEncoder):
    def default(self, obj):
        if isinstance(obj, datetime):
            return obj.isoformat()
        return super().default(obj)


def login_required(handler):
    """Decorator to require authentication"""

    async def decorated(request, *args, **kwargs):
        if 'user' not in request:
            return web.json_response(
                {"error": "Authentication required"},
                status=401
            )
        return await handler(request, *args, **kwargs)

    return decorated


@login_required
async def create_ad_handler(request):
    """Create a new ad"""
    try:
        data = await request.json()
        user = request['user']
        errors = validate_ad_creation(data)
        if errors:
            return web.json_response(
                {"errors": errors},
                status=400
            )

        ad_data = {
            'title': data['title'],
            'description': data.get('description', ''),
            'owner_id': user['id'],
            'created_at': datetime.utcnow()
        }

        ad_id = await create_ad(ad_data)

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
        return web.json_response(
            {"error": "Invalid JSON"},
            status=400
        )
    except Exception as e:
        return web.json_response(
            {"error": "Internal server error"},
            status=500
        )


async def get_ad_handler(request):
    """Get ad by ID"""
    try:
        ad_id = int(request.match_info['id'])
        ad = await get_ad(ad_id)

        if not ad:
            return web.json_response(
                {"error": "Ad not found"},
                status=404
            )

        return web.json_response(
            ad,
            dumps=lambda x: json.dumps(x, cls=DateTimeEncoder)
        )

    except ValueError:
        return web.json_response(
            {"error": "Invalid ad ID"},
            status=400
        )
    except Exception as e:
        return web.json_response(
            {"error": "Internal server error"},
            status=500
        )


async def get_ads_handler(request):
    """Get all ads"""
    try:
        ads = await get_all_ads()

        return web.json_response(
            ads,
            dumps=lambda x: json.dumps(x, cls=DateTimeEncoder)
        )

    except Exception as e:
        return web.json_response(
            {"error": "Internal server error"},
            status=500
        )


@login_required
async def update_ad_handler(request):
    """Update existing ad"""
    try:
        ad_id = int(request.match_info['id'])
        data = await request.json()
        user = request['user']
        ad = await get_ad(ad_id)
        if not ad:
            return web.json_response(
                {"error": "Ad not found"},
                status=404
            )

        if ad['owner_id'] != user['id']:
            return web.json_response(
                {"error": "You can only update your own ads"},
                status=403
            )

        errors = validate_ad_update(data)
        if errors:
            return web.json_response(
                {"errors": errors},
                status=400
            )

        update_data = {}
        allowed_fields = ['title', 'description']

        for field in allowed_fields:
            if field in data:
                update_data[field] = data[field]

        if update_data:
            await update_ad(ad_id, update_data)

        return web.json_response(
            {'message': 'Ad updated successfully'},
            dumps=lambda x: json.dumps(x, cls=DateTimeEncoder)
        )

    except ValueError:
        return web.json_response(
            {"error": "Invalid ad ID"},
            status=400
        )
    except json.JSONDecodeError:
        return web.json_response(
            {"error": "Invalid JSON"},
            status=400
        )
    except Exception as e:
        return web.json_response(
            {"error": "Internal server error"},
            status=500
        )


@login_required
async def delete_ad_handler(request):
    """Delete ad"""
    try:
        ad_id = int(request.match_info['id'])
        user = request['user']
        ad = await get_ad(ad_id)
        if not ad:
            return web.json_response(
                {"error": "Ad not found"},
                status=404
            )

        if ad['owner_id'] != user['id']:
            return web.json_response(
                {"error": "You can only delete your own ads"},
                status=403
            )

        await delete_ad(ad_id)

        return web.json_response(
            {'message': 'Ad deleted successfully'},
            dumps=lambda x: json.dumps(x, cls=DateTimeEncoder)
        )

    except ValueError:
        return web.json_response(
            {"error": "Invalid ad ID"},
            status=400
        )
    except Exception as e:
        return web.json_response(
            {"error": "Internal server error"},
            status=500
        )