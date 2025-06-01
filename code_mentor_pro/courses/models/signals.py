from django.db.models.signals import post_save
from django.dispatch import receiver

from courses.models import UserCourse, UserCourseLesson, UserCourseSurvey
from courses.tasks import check_user_achievements_task


@receiver(post_save, sender=UserCourse)
def handle_user_course_enrolled(sender, instance, created, **kwargs):
    if created:
        check_user_achievements_task.delay(instance.user.id)


@receiver(post_save, sender=UserCourseSurvey)
def handle_survey_completed(sender, instance, **kwargs):
    if instance.status == instance.STATUS_COMPLETED:
        check_user_achievements_task.delay(instance.user_course.user.id)


@receiver(post_save, sender=UserCourseLesson)
def handle_lesson_completed(sender, instance, **kwargs):
    if instance.status == instance.STATUS_COMPLETED:
        check_user_achievements_task.delay(instance.user_course.user.id)
