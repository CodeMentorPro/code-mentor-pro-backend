from django.db.models import Prefetch
from rest_framework import status
from rest_framework.generics import get_object_or_404
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework.viewsets import ReadOnlyModelViewSet

from courses.models import (Course, Lesson, Material, Module, UserCourse,
                            UserCourseLesson, UserCourseLessonMaterial)

from .serializers import (CourseDetailSerializer, CourseSerializer,
                          CourseSerializerForAuthUser, LessonDetailSerializer)


class CourseViewSet(ReadOnlyModelViewSet):
    queryset = Course.objects.filter(is_published=True)
    serializer_class = CourseSerializer
    permission_classes = [AllowAny]

    def list(self, request, *args, **kwargs):
        queryset = self.filter_queryset(self.get_queryset())

        page = self.paginate_queryset(queryset)
        if page is not None:
            serializer = self.get_serializer(page, many=True)
            return self.get_paginated_response(serializer.data)

        if request.user and request.user.is_authenticated:
            serializer = CourseSerializerForAuthUser(
                queryset, many=True, context={"request": request}
            )
        else:
            serializer = self.get_serializer(queryset, many=True)
        return Response(serializer.data)


class CourseDetailView(APIView):
    permission_classes = [AllowAny]

    def get(self, request, slug):
        course = get_object_or_404(
            Course.objects.prefetch_related(
                Prefetch(
                    "modules",
                    queryset=Module.objects.order_by("order").prefetch_related(
                        Prefetch("lessons", queryset=Lesson.objects.order_by("order"))
                    ),
                )
            ),
            slug=slug,
        )

        if request.user and request.user.is_authenticated:
            user_course_lessons = []
            user_course = UserCourse.objects.get(user=request.user, course=course)
            for module in course.modules.all():
                for lesson in module.lessons.all():
                    if not UserCourseLesson.objects.filter(
                        user_course=user_course, lesson=lesson
                    ).exists():
                        _lesson = UserCourseLesson(
                            user_course=user_course, lesson=lesson
                        )
                        user_course_lessons.append(_lesson)
            if user_course_lessons:
                UserCourseLesson.objects.bulk_create(user_course_lessons)

            # При входе на курс - зачисляем пользователя
            course.enroll_user(request.user)

        serializer = CourseDetailSerializer(course, context={"request": request})
        return Response({"course": serializer.data})


class LessonDetailView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request, course_slug, lesson_id):
        course = get_object_or_404(Course, slug=course_slug)
        lesson = get_object_or_404(
            Lesson.objects.prefetch_related("materials"),
            id=lesson_id,
            module__course=course,
        )

        user_course_lesson = UserCourseLesson.objects.filter(
            user_course__user=request.user, lesson=lesson
        ).first()
        if (
            user_course_lesson
            and user_course_lesson.status == UserCourseLesson.STATUS_NOT_VIEWED
        ):
            user_course_lesson.status = UserCourseLesson.STATUS_VIEWED
            user_course_lesson.save()

        user_course_lessons_materials = []
        for material in lesson.materials.all():
            if not UserCourseLessonMaterial.objects.filter(
                user_course_lesson=user_course_lesson, material=material
            ).exists():
                _material = UserCourseLessonMaterial(
                    user_course_lesson=user_course_lesson, material=material
                )
                user_course_lessons_materials.append(_material)
        if user_course_lessons_materials:
            UserCourseLessonMaterial.objects.bulk_create(user_course_lessons_materials)

        serializer = LessonDetailSerializer(
            lesson, context={"request": request, "lesson": lesson}
        )
        return Response({"lesson": serializer.data}, status=status.HTTP_200_OK)


class CompleteMaterialView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request, course_slug, lesson_id, material_id):
        # 1. Проверяем существование курса, урока и материала
        course = get_object_or_404(Course, slug=course_slug)
        lesson = get_object_or_404(Lesson, id=lesson_id, module__course=course)
        material = get_object_or_404(Material, id=material_id, lesson=lesson)

        # 2. Получаем или создаем user_course
        user_course = course.enroll_user(request.user)

        # 3. Получаем или создаем user_course_lesson
        user_course_lesson, _ = UserCourseLesson.objects.get_or_create(
            user_course=user_course, lesson=lesson
        )

        # 4. Получаем или создаем user_course_lesson_material
        uclm, _ = UserCourseLessonMaterial.objects.get_or_create(
            user_course_lesson=user_course_lesson,
            material=material,
        )

        # 5. Меняем статус
        uclm.status = UserCourseLessonMaterial.STATUS_COMPLETED
        uclm.save()

        if user_course_lesson.status == UserCourseLesson.STATUS_VIEWED:
            user_course_lesson.status = UserCourseLesson.STATUS_IN_PROGRESS
            user_course_lesson.save()

        return Response(
            {"detail": "Материал отмечен как завершённый."}, status=status.HTTP_200_OK
        )
