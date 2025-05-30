from django.db.models import Prefetch
from django.utils import timezone
from rest_framework import status
from rest_framework.generics import get_object_or_404
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework.viewsets import ReadOnlyModelViewSet

from courses.models import (AnswerOption, Course, Lesson, Material, Module,
                            Question, Survey, UserAnswer, UserCourse,
                            UserCourseLesson, UserCourseLessonMaterial,
                            UserCourseSurvey)

from .serializers import (CourseDetailSerializer, CourseSerializer,
                          CourseSerializerForAuthUser, LessonDetailSerializer,
                          SurveySerializer)


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
        user_course = course.enroll_user(request.user)

        # Создаем связку юзер - урок
        user_course_lesson = UserCourseLesson.objects.filter(
            user_course__user=request.user, lesson=lesson
        ).first()
        if (
            user_course_lesson
            and user_course_lesson.status == UserCourseLesson.STATUS_NOT_VIEWED
        ):
            user_course_lesson.status = UserCourseLesson.STATUS_VIEWED
            user_course_lesson.save()

        # Создаем связку юзер - урок - материал
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


class SaveSurveyAnswersView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request, course_slug, lesson_id, survey_id):
        data = request.data
        user = request.user

        course = get_object_or_404(Course, slug=course_slug)
        lesson = get_object_or_404(Lesson, id=lesson_id, module__course=course)
        survey = get_object_or_404(Survey, id=survey_id, lessons__id=lesson.id)

        user_course = UserCourse.objects.filter(course=course, user=user).first()
        if not user_course:
            user_course = course.enroll_user(user)

        user_survey, _ = UserCourseSurvey.objects.get_or_create(
            user_course=user_course, survey=survey
        )

        incoming_question_ids = set()

        for question_data in data.get("questions", []):
            question_id = question_data.get("question_id")
            answer_ids = question_data.get("answers", [])
            incoming_question_ids.add(question_id)

            question = get_object_or_404(Question, id=question_id, survey=survey)
            correct_option_ids = set(
                question.options.filter(is_correct=True).values_list("id", flat=True)
            )

            answer_objs = AnswerOption.objects.filter(
                id__in=answer_ids, question=question
            )

            user_answer, _ = UserAnswer.objects.get_or_create(
                user_survey=user_survey, question=question
            )
            user_answer.selected_options.set(answer_objs)

            selected_ids = set(answer_objs.values_list("id", flat=True))

            if not selected_ids:
                user_answer.status = UserAnswer.STATUS_NOT_COMPLETED_YET
            elif selected_ids == correct_option_ids:
                user_answer.status = UserAnswer.STATUS_COMPLETED
            else:
                user_answer.status = UserAnswer.STATUS_COMPLETED_WITH_FAILS

            user_answer.save()

        UserAnswer.objects.filter(user_survey=user_survey).exclude(
            question_id__in=incoming_question_ids
        ).delete()

        answers = user_survey.answers.all()
        if any(ans.status == UserAnswer.STATUS_NOT_COMPLETED_YET for ans in answers):
            user_survey.status = UserCourseSurvey.STATUS_NOT_COMPLETED_YET
        elif any(
            ans.status == UserAnswer.STATUS_COMPLETED_WITH_FAILS for ans in answers
        ):
            user_survey.status = UserCourseSurvey.STATUS_COMPLETED_WITH_FAILS
        else:
            user_survey.status = UserCourseSurvey.STATUS_COMPLETED

        user_survey.completed_at = timezone.now()
        user_survey.save()

        # ⬇️ Обновление статуса урока
        user_course_lesson, _ = UserCourseLesson.objects.get_or_create(
            user_course=user_course, lesson=lesson
        )

        lesson_surveys = lesson.surveys.all()
        if not lesson_surveys.exists():
            # если нет опросов вообще — считаем завершенным
            user_course_lesson.status = UserCourseLesson.STATUS_COMPLETED
        else:
            # получаем все user-связки для опросов этого урока
            user_surveys = UserCourseSurvey.objects.filter(
                user_course=user_course, survey__in=lesson_surveys
            )

            if user_surveys.count() < lesson_surveys.count():
                # пользователь еще не ответил на все опросы
                user_course_lesson.status = UserCourseLesson.STATUS_IN_PROGRESS
            elif all(
                s.status == UserCourseSurvey.STATUS_COMPLETED for s in user_surveys
            ):
                user_course_lesson.status = UserCourseLesson.STATUS_COMPLETED
            else:
                user_course_lesson.status = UserCourseLesson.STATUS_IN_PROGRESS

        user_course_lesson.save()

        survey_data = SurveySerializer(survey, context={"request": self.request}).data
        return Response(survey_data, status=status.HTTP_200_OK)
