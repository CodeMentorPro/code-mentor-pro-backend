from django.conf import settings
from django.urls import path
from rest_framework.routers import DefaultRouter, SimpleRouter

from code_mentor_pro.users.api.views import RegistrationView, UserProfileView
from courses.api.views import (CompleteMaterialView, CourseDetailView,
                               CourseViewSet, LessonDetailView,
                               SaveSurveyAnswersView, UserProgressDetailView)

router = DefaultRouter() if settings.DEBUG else SimpleRouter()


app_name = "api"
urlpatterns = router.urls + [
    path("auth/register/", RegistrationView.as_view(), name="user-register"),
    path("users/profile/", UserProfileView.as_view(), name="user-profile"),
    path("users/progress", UserProgressDetailView.as_view(), name="user-progress"),
    # КУРСЫ
    path("courses/", CourseViewSet.as_view({"get": "list"}), name="course-list"),
    path("courses/<slug:slug>/", CourseDetailView.as_view(), name="course-detail"),
    path(
        "courses/<slug:course_slug>/lessons/<int:lesson_id>/",
        LessonDetailView.as_view(),
        name="lesson-detail",
    ),
    path(
        "courses/<slug:course_slug>/lessons/<int:lesson_id>/materials/<int:material_id>/complete",
        CompleteMaterialView.as_view(),
        name="complete-material",
    ),
    # ОПРОСЫ
    path(
        "courses/<slug:course_slug>/lessons/<int:lesson_id>/surveys/<int:survey_id>/save_answers",
        SaveSurveyAnswersView.as_view(),
        name="save-survey-answers",
    ),
]
