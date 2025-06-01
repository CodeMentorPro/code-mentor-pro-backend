def has_enrolled_in_first_course(user) -> bool:
    """
    Пользователь зачислен на свой первый курс
    """
    from courses.models import UserCourse

    return UserCourse.objects.filter(user=user).exists()


def has_completed_first_survey(user) -> bool:
    """
    Пользователь прошел свой первый опрос
    """
    from courses.models import UserCourseSurvey

    return UserCourseSurvey.objects.filter(
        user_course__user=user, status=UserCourseSurvey.STATUS_COMPLETED
    ).exists()


def has_completed_first_lesson(user) -> bool:
    """
    Пользователь прошел свой первый урок
    """
    from courses.models import UserCourseLesson

    return UserCourseLesson.objects.filter(
        user_course__user=user, status=UserCourseLesson.STATUS_COMPLETED
    ).exists()


def has_completed_five_surveys(user) -> bool:
    from courses.models import UserCourseSurvey

    return (
        UserCourseSurvey.objects.filter(
            user_course__user=user, status=UserCourseSurvey.STATUS_COMPLETED
        ).count()
        >= 5
    )


def has_completed_ten_surveys(user) -> bool:
    from courses.models import UserCourseSurvey

    return (
        UserCourseSurvey.objects.filter(
            user_course__user=user, status=UserCourseSurvey.STATUS_COMPLETED
        ).count()
        >= 10
    )


def has_completed_five_lessons(user) -> bool:
    from courses.models import UserCourseLesson

    return (
        UserCourseLesson.objects.filter(
            user_course__user=user, status=UserCourseLesson.STATUS_COMPLETED
        ).count()
        >= 5
    )


def has_completed_ten_lessons(user) -> bool:
    from courses.models import UserCourseLesson

    return (
        UserCourseLesson.objects.filter(
            user_course__user=user, status=UserCourseLesson.STATUS_COMPLETED
        ).count()
        >= 10
    )
