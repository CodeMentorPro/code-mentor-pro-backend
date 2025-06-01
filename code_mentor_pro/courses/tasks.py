from celery import shared_task
from django.contrib.auth import get_user_model

from courses.models import Achievement

User = get_user_model()


@shared_task
def check_user_achievements_task(user_id):
    try:
        user = User.objects.get(pk=user_id)
    except User.DoesNotExist:
        return

    for achievement in Achievement.objects.filter(is_active=True):
        achievement.check_for_user(user)
