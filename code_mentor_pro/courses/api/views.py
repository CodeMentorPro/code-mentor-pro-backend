from django.db.models import Prefetch
from rest_framework import status
from rest_framework.generics import get_object_or_404
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework.viewsets import ReadOnlyModelViewSet

from courses.models import Course, Lesson, Module

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
    permission_classes = [IsAuthenticated]

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

        serializer = LessonDetailSerializer(lesson, context={"request": request})
        return Response({"lesson": serializer.data}, status=status.HTTP_200_OK)
