from rest_framework import serializers

from courses.models import (Course, Lesson, Material, Module, UserCourseLesson,
                            UserCourseLessonMaterial)


class CourseSerializer(serializers.ModelSerializer):
    class Meta:
        model = Course
        fields = "__all__"


class CourseSerializerForAuthUser(serializers.ModelSerializer):
    is_enrolled = serializers.SerializerMethodField()

    class Meta:
        model = Course
        fields = "__all__"

    def get_is_enrolled(self, obj):
        user = self.context["request"].user
        if user.is_authenticated:
            return user.user_courses.filter(course=obj).exists()
        return False


class LessonSerializer(serializers.ModelSerializer):
    status = serializers.SerializerMethodField()

    class Meta:
        model = Lesson
        fields = ["id", "title", "description", "order", "status"]

    def get_status(self, obj):
        if self.context and "request" in self.context:
            request = self.context["request"]
            user = request.user
            if user and user.is_authenticated:
                user_course_lesson = UserCourseLesson.objects.filter(
                    user_course__user=user, lesson=obj
                ).first()
                if user_course_lesson:
                    return user_course_lesson.status
        return None


class ModuleSerializer(serializers.ModelSerializer):
    lessons = LessonSerializer(many=True, read_only=True)

    class Meta:
        model = Module
        fields = ["id", "title", "description", "order", "lessons"]


class CourseDetailSerializer(serializers.ModelSerializer):
    modules = ModuleSerializer(many=True, read_only=True)

    class Meta:
        model = Course
        fields = [
            "id",
            "title",
            "description",
            "logo",
            "programming_language",
            "level",
            "slug",
            "is_published",
            "certificate_available",
            "main_color",
            "modules",
        ]


class MaterialSerializer(serializers.ModelSerializer):
    status = serializers.SerializerMethodField()

    class Meta:
        model = Material
        fields = [
            "id",
            "title",
            "description",
            "language",
            "link",
            "material_type",
            "status",
        ]

    def get_status(self, obj):
        if self.context and "request" in self.context and "lesson" in self.context:
            request = self.context["request"]
            user = request.user
            if user and user.is_authenticated:
                user_course_lesson_material = UserCourseLessonMaterial.objects.filter(
                    user_course_lesson__user_course__user=user,
                    user_course_lesson__lesson=self.context["lesson"],
                    material=obj,
                ).first()
                if user_course_lesson_material:
                    return user_course_lesson_material.status
        return None


class LessonDetailSerializer(serializers.ModelSerializer):
    materials = MaterialSerializer(many=True, read_only=True)

    class Meta:
        model = Lesson
        fields = ["id", "title", "description", "order", "materials"]
