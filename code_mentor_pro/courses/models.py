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
    user = models.ForeignKey(
        User, on_delete=models.CASCADE, related_name="user_courses"
    )
    course = models.ForeignKey(
        Course, on_delete=models.CASCADE, related_name="user_courses"
    )


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
    order = models.PositiveIntegerField(default=0)

    class Meta:
        ordering = ["order"]

    def __str__(self):
        return f"{self.module} - {self.order}. {self.title}"


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
