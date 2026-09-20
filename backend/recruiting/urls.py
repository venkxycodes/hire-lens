from django.urls import include, path
from rest_framework.routers import DefaultRouter

from .views import ApplicationViewSet, CompareResumeView, JobViewSet, LoginView, RubricDraftView, SessionView

router = DefaultRouter()
router.register("jobs", JobViewSet, basename="job")
router.register("applications", ApplicationViewSet, basename="application")
urlpatterns = [
    path("session/", SessionView.as_view()),
    path("login/", LoginView.as_view()),
    path("compare/", CompareResumeView.as_view()),
    path("rubric-draft/", RubricDraftView.as_view()),
    path("", include(router.urls)),
]
