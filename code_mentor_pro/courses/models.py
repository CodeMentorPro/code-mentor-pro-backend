from django.db import models
from django.utils.text import slugify

from code_mentor_pro.users.models import User
from common.models import SimpleBaseModel


class Course(SimpleBaseModel):
    PROGRAMMING_LANGUAGE_PYTHON = "PROGRAMMING_LANGUAGE_PYTHON"
    LANGUAGE_CHOICES = [
        (PROGRAMMING_LANGUAGE_PYTHON, "Python"),
    ]

    LEVEL_BEGINNER = "LEVEL_BEGINNER"
    LEVEL_INTERMEDIATE = "LEVEL_INTERMEDIATE"
    LEVEL_ADVANCED = "LEVEL_ADVANCED"
    LEVEL_CHOICES = [
        (LEVEL_BEGINNER, "Начальный"),
        (LEVEL_INTERMEDIATE, "Средний"),
        (LEVEL_ADVANCED, "Продвинутый"),
    ]

    title = models.CharField(max_length=255)
    short_description = models.CharField(max_length=255, null=True, blank=True)
    description = models.TextField()
    logo = models.ImageField(upload_to="courses/logos/")
    programming_language = models.CharField(
        max_length=50, choices=LANGUAGE_CHOICES, blank=True, null=True
    )
    level = models.CharField(
        max_length=20, choices=LEVEL_CHOICES, blank=True, null=True
    )
    slug = models.SlugField(unique=True, blank=True)
    is_published = models.BooleanField(default=False)
    certificate_available = models.BooleanField(default=False)
    main_color = models.CharField(
        max_length=20, blank=True, null=True, help_text="HEX color code"
    )

    def enroll_user(self, user: User) -> "UserCourse":
        if user.user_courses.filter(course=self).exists():
            return user.user_courses.get(course=self)
        return UserCourse.objects.create(user=user, course=self)

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.title)
        super().save(*args, **kwargs)

    def __str__(self):
        return self.title


class UserCourse(SimpleBaseModel):
    class Meta:
        unique_together = ("user", "course")

    user = models.ForeignKey(
        User, on_delete=models.CASCADE, related_name="user_courses"
    )
    course = models.ForeignKey(
        Course, on_delete=models.CASCADE, related_name="user_courses"
    )

    def get_progress_details(self):
        """
        Возвращает прогресс пользователя по курсу:
        - total_lessons: всего уроков
        - completed_lessons: завершенные (по статусу или все опросы завершены)
        - total_surveys: всего опросов
        - completed_surveys: завершённые пользователем
        - progress_percent: общий прогресс по урокам и опросам
        """
        lessons = Lesson.objects.filter(module__course=self.course).prefetch_related("surveys")
        total_lessons = lessons.count()
        completed_lessons = 0
        total_surveys = 0
        completed_surveys = 0

        for lesson in lessons:
            surveys = list(lesson.surveys.all())
            survey_ids = [s.id for s in surveys]

            # Подсчёт опросов
            total_surveys += len(survey_ids)

            completed_count = UserCourseSurvey.objects.filter(
                user_course=self,
                survey_id__in=survey_ids,
                status=UserCourseSurvey.STATUS_COMPLETED,
            ).count()
            completed_surveys += completed_count

            # Урок считается завершенным если:
            # - нет опросов и статус lesson == COMPLETED
            # - или все опросы завершены
            if not survey_ids:
                lesson_status = UserCourseLesson.objects.filter(
                    user_course=self, lesson=lesson,
                    status=UserCourseLesson.STATUS_COMPLETED,
                ).exists()
                if lesson_status:
                    completed_lessons += 1
            elif completed_count == len(survey_ids):
                completed_lessons += 1

        total_steps = total_lessons + total_surveys
        completed_steps = completed_lessons + completed_surveys

        progress_percent = round(completed_steps / total_steps * 100) if total_steps else 0

        return {
            "total_lessons": total_lessons,
            "completed_lessons": completed_lessons,
            "total_surveys": total_surveys,
            "completed_surveys": completed_surveys,
            "progress_percent": progress_percent,
        }


    def get_progress_percent(self):
        """
        Возвращает только процент прохождения курса.
        """
        details = self.get_progress_details()
        return details["progress_percent"]


class Module(SimpleBaseModel):
    course = models.ForeignKey(Course, on_delete=models.CASCADE, related_name="modules")
    title = models.CharField(max_length=255)
    description = models.TextField(blank=True)
    order = models.PositiveIntegerField(default=0)

    class Meta:
        ordering = ["order"]

    def __str__(self):
        return f"{self.course.title} - {self.order}. {self.title}"


class Lesson(SimpleBaseModel):
    module = models.ForeignKey(Module, on_delete=models.CASCADE, related_name="lessons")
    title = models.CharField(max_length=255)
    description = models.TextField(blank=True)
    surveys = models.ManyToManyField("Survey", blank=True, related_name="lessons")
    order = models.PositiveIntegerField(default=0)

    class Meta:
        ordering = ["order"]

    def __str__(self):
        return f"{self.module} - {self.order}. {self.title}"


class UserCourseLesson(SimpleBaseModel):
    class Meta:
        unique_together = ("user_course", "lesson")

    STATUS_NOT_VIEWED = "STATUS_NOT_VIEWED"
    STATUS_VIEWED = "STATUS_VIEWED"
    STATUS_IN_PROGRESS = "STATUS_IN_PROGRESS"
    STATUS_COMPLETED = "STATUS_COMPLETED"
    STATUS_CHOICES = (
        (STATUS_NOT_VIEWED, "Не просмотрено"),
        (STATUS_VIEWED, "Просмотрено"),
        (STATUS_IN_PROGRESS, "В процессе"),
        (STATUS_COMPLETED, "Завершен"),
    )

    user_course = models.ForeignKey(
        UserCourse, on_delete=models.CASCADE, related_name="lessons"
    )
    lesson = models.ForeignKey(Lesson, on_delete=models.CASCADE)
    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default=STATUS_NOT_VIEWED,
    )

    def __str__(self):
        return f"{self.user_course} - {self.lesson}"


class Material(SimpleBaseModel):
    LANGUAGE_RU = "LANGUAGE_RU"
    LANGUAGE_ENG = "LANGUAGE_ENG"
    LANGUAGE_CHOICES = [
        (LANGUAGE_RU, "Русский"),
        (LANGUAGE_ENG, "Английский"),
    ]

    MATERIAL_TYPE_TEXT = "MATERIAL_TYPE_TEXT"
    MATERIAL_TYPE_VIDEO = "MATERIAL_TYPE_VIDEO"
    MATERIAL_TYPE_COURSE = "MATERIAL_TYPE_COURSE"
    MATERIAL_TYPE_CHOICES = [
        (MATERIAL_TYPE_TEXT, "Текст"),
        (MATERIAL_TYPE_VIDEO, "Видео"),
        (MATERIAL_TYPE_COURSE, "Курс"),
    ]

    lesson = models.ForeignKey(
        Lesson, on_delete=models.CASCADE, related_name="materials"
    )
    title = models.CharField(max_length=255)
    description = models.TextField(blank=True)
    language = models.CharField(max_length=20, choices=LANGUAGE_CHOICES)
    link = models.URLField(blank=True, null=True)
    material_type = models.CharField(max_length=20, choices=MATERIAL_TYPE_CHOICES)

    def __str__(self):
        return f"{self.title}"


class UserCourseLessonMaterial(SimpleBaseModel):
    class Meta:
        unique_together = ("user_course_lesson", "material")

    STATUS_NOT_COMPLETED = "STATUS_NOT_COMPLETED"
    STATUS_COMPLETED = "STATUS_COMPLETED"
    STATUS_CHOICES = (
        (STATUS_NOT_COMPLETED, "Не завершено"),
        (STATUS_COMPLETED, "Завершено"),
    )

    user_course_lesson = models.ForeignKey(
        UserCourseLesson, on_delete=models.CASCADE, related_name="materials"
    )
    material = models.ForeignKey(Material, on_delete=models.CASCADE)
    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default=STATUS_NOT_COMPLETED,
    )

    def __str__(self):
        return f"{self.user_course_lesson} - {self.material}"


class Survey(SimpleBaseModel):
    title = models.CharField(max_length=255)
    description = models.TextField(blank=True)
    is_active = models.BooleanField(default=True)


class Question(SimpleBaseModel):
    survey = models.ForeignKey(
        Survey, on_delete=models.CASCADE, related_name="questions"
    )
    text = models.TextField()
    is_multiple_choice = models.BooleanField(default=False)
    order = models.PositiveIntegerField(default=0)

    class Meta:
        ordering = ["order"]


class AnswerOption(SimpleBaseModel):
    question = models.ForeignKey(
        Question, on_delete=models.CASCADE, related_name="options"
    )
    text = models.CharField(max_length=255)
    is_correct = models.BooleanField(default=False)


class UserCourseSurvey(SimpleBaseModel):
    STATUS_NOT_COMPLETED_YET = "STATUS_NOT_COMPLETED_YET"
    STATUS_COMPLETED_WITH_FAILS = "STATUS_COMPLETED_WITH_FAILS"
    STATUS_COMPLETED = "STATUS_COMPLETED"
    STATUS_CHOICES = (
        (STATUS_NOT_COMPLETED_YET, "Не завершен"),
        (STATUS_COMPLETED_WITH_FAILS, "Завершен с ошибками"),
        (STATUS_COMPLETED, "Завершен"),
    )

    user_course = models.ForeignKey(
        UserCourse, on_delete=models.CASCADE, related_name="surveys"
    )
    survey = models.ForeignKey(
        Survey, on_delete=models.CASCADE, related_name="user_course_surveys"
    )
    status = models.CharField(
        max_length=30,
        choices=STATUS_CHOICES,
        default=STATUS_NOT_COMPLETED_YET,
    )
    completed_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        unique_together = ("user_course", "survey")


class UserAnswer(SimpleBaseModel):
    STATUS_NOT_COMPLETED_YET = "STATUS_NOT_COMPLETED_YET"
    STATUS_COMPLETED_WITH_FAILS = "STATUS_COMPLETED_WITH_FAILS"
    STATUS_COMPLETED = "STATUS_COMPLETED"
    STATUS_CHOICES = (
        (STATUS_NOT_COMPLETED_YET, "Не отвечено"),
        (STATUS_COMPLETED_WITH_FAILS, "Отвечено неверно"),
        (STATUS_COMPLETED, "Отвечено правильно"),
    )

    user_survey = models.ForeignKey(
        UserCourseSurvey, on_delete=models.CASCADE, related_name="answers"
    )
    question = models.ForeignKey(Question, on_delete=models.CASCADE)
    selected_options = models.ManyToManyField(AnswerOption)
    status = models.CharField(
        max_length=30,
        choices=STATUS_CHOICES,
        default=STATUS_NOT_COMPLETED_YET,
    )

    class Meta:
        unique_together = ("user_survey", "question")
