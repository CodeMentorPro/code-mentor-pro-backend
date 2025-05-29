from django.conf import settings
from django.urls import path
from rest_framework.routers import DefaultRouter, SimpleRouter

from code_mentor_pro.users.api.views import RegistrationView, UserProfileView
from courses.api.views import CourseDetailView, CourseViewSet, LessonDetailView

router = DefaultRouter() if settings.DEBUG else SimpleRouter()


app_name = "api"
urlpatterns = router.urls + [
    path("auth/register/", RegistrationView.as_view(), name="user-register"),
    path("users/profile/", UserProfileView.as_view(), name="user-profile"),
    # КУРСЫ
    path("courses/", CourseViewSet.as_view({"get": "list"}), name="course-list"),
    path("courses/<slug:slug>/", CourseDetailView.as_view(), name="course-detail"),
    path(
        "courses/<slug:course_slug>/lessons/<int:lesson_id>/",
        LessonDetailView.as_view(),
        name="lesson-detail",
    ),
]
