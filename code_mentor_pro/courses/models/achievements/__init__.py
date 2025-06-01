from django.db import models
from django.utils.translation import gettext_lazy as _

from code_mentor_pro.users.models import User
from common.models import SimpleBaseModel

from .checks import (has_completed_first_lesson, has_completed_first_survey,
                     has_completed_five_lessons, has_completed_five_surveys,
                     has_completed_ten_lessons, has_completed_ten_surveys,
                     has_enrolled_in_first_course)


class Achievement(SimpleBaseModel):
    class AchievementCode(models.TextChoices):
        ENROLL_FIRST_COURSE = "ENROLL_FIRST_COURSE", _("Зачислиться на 1 курс")

        COMPLETE_FIRST_SURVEY = "COMPLETE_FIRST_SURVEY", _("Пройти 1 опрос")
        COMPLETE_FIVE_SURVEYS = "COMPLETE_FIVE_SURVEYS", _("Пройти 5 опросов")
        COMPLETE_TEN_SURVEYS = "COMPLETE_TEN_SURVEYS", _("Пройти 10 опросов")

        COMPLETE_FIRST_LESSON = "COMPLETE_FIRST_LESSON", _("Пройти 1 урок")
        COMPLETE_FIVE_LESSONS = "COMPLETE_FIVE_LESSONS", _("Пройти 5 уроков")
        COMPLETE_TEN_LESSONS = "COMPLETE_TEN_LESSONS", _("Пройти 10 уроков")

    ACHIEVEMENT_CHECKS = {
        AchievementCode.ENROLL_FIRST_COURSE: has_enrolled_in_first_course,
        AchievementCode.COMPLETE_FIRST_SURVEY: has_completed_first_survey,
        AchievementCode.COMPLETE_FIVE_SURVEYS: has_completed_five_surveys,
        AchievementCode.COMPLETE_TEN_SURVEYS: has_completed_ten_surveys,
        AchievementCode.COMPLETE_FIRST_LESSON: has_completed_first_lesson,
        AchievementCode.COMPLETE_FIVE_LESSONS: has_completed_five_lessons,
        AchievementCode.COMPLETE_TEN_LESSONS: has_completed_ten_lessons,
    }

    code = models.CharField(max_length=64, choices=AchievementCode.choices, unique=True)
    title = models.CharField(max_length=255)
    description = models.TextField(blank=True)
    icon = models.ImageField(upload_to="achievements/icons/", blank=True, null=True)
    is_active = models.BooleanField(default=True)

    def check_for_user(self, user) -> bool:
        """
        Проверяет, получено ли достижение, и если нет — запускает проверку условия.

        Возвращает True, если достижение получено или только что присвоено.
        """

        if UserAchievement.objects.filter(user=user, achievement=self).exists():
            return True

        check_fn = self.ACHIEVEMENT_CHECKS.get(self.code)
        if check_fn and check_fn(user):
            UserAchievement.objects.create(user=user, achievement=self)
            return True

        return False

    def __str__(self):
        return self.title


class UserAchievement(SimpleBaseModel):
    user = models.ForeignKey(
        User, on_delete=models.CASCADE, related_name="achievements"
    )
    achievement = models.ForeignKey(Achievement, on_delete=models.CASCADE)
    awarded_at = models.DateTimeField(auto_now_add=True)
    is_notified = models.BooleanField(default=False)

    class Meta:
        unique_together = ("user", "achievement")

    def __str__(self):
        return f"{self.user} — {self.achievement.code}"
