from django.db import models
from django.utils.text import slugify

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

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.title)
        super().save(*args, **kwargs)

    def __str__(self):
        return self.title
