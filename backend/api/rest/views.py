from django.conf import settings
from rest_framework import status
from rest_framework.request import Request
from rest_framework.response import Response
from rest_framework.views import APIView


class HealthView(APIView):
    authentication_classes = []
    permission_classes = []

    def get(self, request: Request) -> Response:
        return Response({"status": "ok"})


class InfoView(APIView):
    authentication_classes = []
    permission_classes = []

    def get(self, request: Request) -> Response:
        return Response(
            {
                "name": "django-base-code",
                "version": settings.APP_VERSION,
                "env": settings.ENV,
            }
        )


class EchoView(APIView):
    authentication_classes = []
    permission_classes = []

    def post(self, request: Request) -> Response:
        message = request.data.get("message")
        if not isinstance(message, str) or not message.strip():
            return Response(
                {"error": "message is required"},
                status=status.HTTP_400_BAD_REQUEST,
            )
        return Response({"message": message.strip()})
