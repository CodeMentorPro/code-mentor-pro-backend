from rest_framework import serializers

from courses.models import Course, Lesson, Material, Module


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
    class Meta:
        model = Lesson
        fields = ["id", "title", "description", "order"]


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
    class Meta:
        model = Material
        fields = [
            "id",
            "title",
            "description",
            "language",
            "link",
            "material_type",
        ]


class LessonDetailSerializer(serializers.ModelSerializer):
    materials = MaterialSerializer(many=True, read_only=True)

    class Meta:
        model = Lesson
        fields = ["id", "title", "description", "order", "materials"]
