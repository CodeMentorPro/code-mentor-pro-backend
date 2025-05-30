from django.contrib import admin

from courses.models import (AnswerOption, Course, Lesson, Material, Module,
                            Question, Survey, UserAnswer, UserCourse,
                            UserCourseLesson, UserCourseLessonMaterial,
                            UserCourseSurvey)


@admin.register(Course)
class CourseAdmin(admin.ModelAdmin): ...


class MaterialInline(admin.StackedInline):
    model = Material
    extra = 1
    fields = ["title", "description", "language", "link", "material_type"]
    ordering = ["title"]


class SurveyInline(admin.TabularInline):
    model = Lesson.surveys.through  # через промежуточную таблицу
    extra = 1
    verbose_name = "Опрос"
    verbose_name_plural = "Опросы"
    show_change_link = True  # 🔗 добавляет ссылку на редактирование опроса


@admin.register(Lesson)
class LessonAdmin(admin.ModelAdmin):
    list_display = ["title", "module", "order"]
    inlines = [MaterialInline, SurveyInline]
    ordering = ["module", "order"]
    list_filter = ["module"]
    search_fields = ["title", "description"]


class LessonInline(admin.TabularInline):  # Можно заменить на StackedInline
    model = Lesson
    extra = 1  # Количество пустых форм по умолчанию
    fields = ["title", "description", "order"]
    ordering = ["order"]


@admin.register(Module)
class ModuleAdmin(admin.ModelAdmin):
    list_display = ["title", "course", "order"]
    inlines = [LessonInline]
    ordering = ["course", "order"]
    list_filter = ["course"]
    search_fields = ["title", "description"]


@admin.register(Material)
class MaterialAdmin(admin.ModelAdmin): ...


@admin.register(UserCourse)
class UserCourseAdmin(admin.ModelAdmin): ...


@admin.register(UserCourseLesson)
class UserCourseLessonAdmin(admin.ModelAdmin): ...


@admin.register(UserCourseLessonMaterial)
class UserCourseLessonMaterialAdmin(admin.ModelAdmin): ...


class AnswerOptionInline(admin.TabularInline):
    model = AnswerOption
    extra = 1


@admin.register(Question)
class QuestionAdmin(admin.ModelAdmin):
    inlines = [AnswerOptionInline]
    list_display = ("text", "survey", "is_multiple_choice", "order")
    list_filter = ("survey",)
    search_fields = ("text",)


class QuestionInline(admin.TabularInline):
    model = Question
    extra = 1
    show_change_link = True  # 🔗 делает ссылку на редактирование вопроса


@admin.register(Survey)
class SurveyAdmin(admin.ModelAdmin):
    inlines = [QuestionInline]
    list_display = ("title", "is_active")
    search_fields = ("title",)
    list_filter = ("is_active",)


@admin.register(AnswerOption)
class AnswerOptionAdmin(admin.ModelAdmin):
    list_display = ("text", "question", "is_correct")
    list_filter = ("question", "is_correct")
    search_fields = ("text",)


@admin.register(UserCourseSurvey)
class UserCourseSurveyAdmin(admin.ModelAdmin):
    list_display = ("user_course", "survey", "status", "created_at")
    list_filter = ("survey",)
    search_fields = ("user_course__user__username",)


@admin.register(UserAnswer)
class UserAnswerAdmin(admin.ModelAdmin):
    list_display = ("user_survey", "question")
    list_filter = ("question__survey",)
    search_fields = ("user_survey__user__username", "question__text")
