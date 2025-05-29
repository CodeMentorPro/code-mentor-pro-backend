from django.contrib import admin

from courses.models import Course, Lesson, Material, Module, UserCourse


@admin.register(Course)
class CourseAdmin(admin.ModelAdmin): ...


class MaterialInline(admin.StackedInline):
    model = Material
    extra = 1
    fields = ["title", "description", "language", "link", "material_type"]
    ordering = ["title"]


@admin.register(Lesson)
class LessonAdmin(admin.ModelAdmin):
    list_display = ["title", "module", "order"]
    inlines = [MaterialInline]
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
