import graphene
from django.conf import settings


class Query(graphene.ObjectType):
    health = graphene.String(description="Service health status.")
    version = graphene.String(description="Application version.")

    def resolve_health(self, info):
        return "ok"

    def resolve_version(self, info):
        return settings.APP_VERSION


class Echo(graphene.Mutation):
    class Arguments:
        message = graphene.String(required=True)

    message = graphene.String()

    def mutate(self, info, message):
        return Echo(message=message.strip())


class Mutation(graphene.ObjectType):
    echo = Echo.Field(description="Echo a message back to the caller.")


schema = graphene.Schema(query=Query, mutation=Mutation)
