"""
ASGI config for accident_advisor project.

It exposes the ASGI callable as a module-level variable named ``application``.

For more information on this file, see
https://docs.djangoproject.com/en/5.2/howto/deployment/asgi/
"""

import os
import django

# Django 설정 모듈을 명시적으로 설정
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "accident_advisor.settings")

# Django 설정 초기화
django.setup()

# Django 초기화 후에 다른 모듈들 import
from django.core.asgi import get_asgi_application
from channels.routing import ProtocolTypeRouter, URLRouter
from channels.auth import AuthMiddlewareStack
from main.routing import websocket_urlpatterns

# Django ASGI application 생성
django_asgi_app = get_asgi_application()

application = ProtocolTypeRouter({
    "http": django_asgi_app,
    "websocket": AuthMiddlewareStack(
        URLRouter(
            websocket_urlpatterns
        )
    ),
})
