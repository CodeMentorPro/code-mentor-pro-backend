from django.conf import settings
from django.urls import path
from rest_framework.routers import DefaultRouter, SimpleRouter

from code_mentor_pro.users.api.views import RegistrationView, UserProfileView

router = DefaultRouter() if settings.DEBUG else SimpleRouter()


app_name = "api"
urlpatterns = router.urls + [
    path("auth/register/", RegistrationView.as_view(), name="user-register"),
    path("users/profile/", UserProfileView.as_view(), name="user-profile"),
]
