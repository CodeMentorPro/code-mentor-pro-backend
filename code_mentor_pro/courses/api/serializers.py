from random import shuffle

from rest_framework import serializers

from courses.models import (Achievement, AnswerOption, Course, Lesson,
                            Material, Module, Question, Survey,
                            UserAchievement, UserAnswer, UserCourseLesson,
                            UserCourseLessonMaterial, UserCourseSurvey)


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


class AnswerOptionSerializer(serializers.ModelSerializer):
    selected_before = serializers.SerializerMethodField()

    class Meta:
        model = AnswerOption
        fields = ["id", "text", "selected_before"]

    def get_selected_before(self, obj):
        if self.context and "request" in self.context:
            user = self.context["request"].user
            if user and user.is_authenticated:
                return UserAnswer.objects.filter(
                    user_survey__user_course__user=user, selected_options=obj
                ).exists()
        return False


class QuestionSerializer(serializers.ModelSerializer):
    options = serializers.SerializerMethodField()
    status = serializers.SerializerMethodField()

    class Meta:
        model = Question
        fields = ["id", "text", "is_multiple_choice", "order", "options", "status"]

    def get_status(self, obj):
        if self.context and "request" in self.context:
            request = self.context["request"]
            user = request.user
            if user and user.is_authenticated:
                user_answer = UserAnswer.objects.filter(
                    user_survey__user_course__user=user, question=obj
                ).first()
                if user_answer:
                    return user_answer.status

    def get_options(self, obj):
        options = list(obj.options.all())
        shuffle(options)

        return AnswerOptionSerializer(options, many=True, context=self.context).data


class SurveySerializer(serializers.ModelSerializer):
    questions = serializers.SerializerMethodField()
    status = serializers.SerializerMethodField()

    class Meta:
        model = Survey
        fields = ["id", "title", "description", "is_active", "questions", "status"]

    def get_status(self, obj):
        if self.context and "request" in self.context:
            user = self.context["request"].user
            if user and user.is_authenticated:
                user_course_survey: UserCourseSurvey = obj.user_course_surveys.filter(
                    user_course__user=user
                ).first()
                if user_course_survey:
                    return user_course_survey.status
        return UserCourseSurvey.STATUS_NOT_COMPLETED_YET

    def get_questions(self, obj):
        # Получаем все вопросы, перемешиваем
        questions = list(obj.questions.all())
        shuffle(questions)

        return QuestionSerializer(questions, many=True, context=self.context).data


class LessonDetailSerializer(serializers.ModelSerializer):
    materials = MaterialSerializer(many=True, read_only=True)
    surveys = SurveySerializer(many=True, read_only=True)

    class Meta:
        model = Lesson
        fields = ["id", "title", "description", "order", "materials", "surveys"]


class CourseProgressSerializer(serializers.Serializer):
    id = serializers.IntegerField()
    title = serializers.CharField()
    slug = serializers.SlugField()
    progress_percent = serializers.IntegerField()


class AchievementShortSerializer(serializers.ModelSerializer):
    awarded = serializers.SerializerMethodField()

    class Meta:
        model = Achievement
        fields = ["id", "title", "icon", "awarded"]

    def get_awarded(self, obj):
        if self.context and "request" in self.context:
            user = self.context["request"].user
            if user and user.is_authenticated:
                return UserAchievement.objects.filter(
                    user=user, achievement=obj
                ).exists()
        return False


class AchievementFullSerializer(serializers.ModelSerializer):
    awarded = serializers.SerializerMethodField()

    class Meta:
        model = Achievement
        fields = ["id", "title", "icon", "description", "awarded"]

    def get_awarded(self, obj):
        if self.context and "request" in self.context:
            user = self.context["request"].user
            if user and user.is_authenticated:
                return UserAchievement.objects.filter(
                    user=user, achievement=obj
                ).exists()
        return False
