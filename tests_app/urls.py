from django.urls import path
from .views import (
    TestListCreateView, TestDetailView,
    EnrollStudentsView, ReleaseAnswersView,
    TestAnalyticsView, StudentBreakdownView,
    AvailableTestsView, StudentTestDetailView,
    StartTestAttemptView, TestAnswerView,
    SubmitTestAttemptView, TestResultView,
    TestSecurityEventView,
)

urlpatterns = [
    # ── Teacher ──────────────────────────────────────────────
    path("",                                    TestListCreateView.as_view(),   name="test-list-create"),
    path("<uuid:pk>/",                          TestDetailView.as_view(),       name="test-detail"),
    path("<uuid:pk>/enroll/",                   EnrollStudentsView.as_view(),   name="test-enroll"),
    path("<uuid:pk>/release-answers/",          ReleaseAnswersView.as_view(),   name="test-release-answers"),
    path("<uuid:pk>/analytics/",               TestAnalyticsView.as_view(),    name="test-analytics"),
    path("<uuid:pk>/analytics/students/",      StudentBreakdownView.as_view(), name="test-student-breakdown"),

    # ── Student ───────────────────────────────────────────────
    path("available/",                          AvailableTestsView.as_view(),   name="tests-available"),
    path("<uuid:pk>/detail/",                   StudentTestDetailView.as_view(),name="test-student-detail"),
    path("<uuid:pk>/start/",                    StartTestAttemptView.as_view(), name="test-start"),
    path("<uuid:pk>/answer/",                   TestAnswerView.as_view(),       name="test-answer"),
    path("<uuid:pk>/submit/",                   SubmitTestAttemptView.as_view(),name="test-submit"),
    path("<uuid:pk>/result/",                   TestResultView.as_view(),       name="test-result"),
    path("<uuid:pk>/event/",                    TestSecurityEventView.as_view(),name="test-event"),
]