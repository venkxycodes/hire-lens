from django.conf import settings
from django.urls import include, path
from graphene_django.views import GraphQLView

urlpatterns = [
    path("api/v1/", include("recruiting.urls")),
    path("api/v1/", include("api.rest.urls")),
    path(
        "graphql/",
        GraphQLView.as_view(graphiql=settings.DEBUG),
    ),
]
