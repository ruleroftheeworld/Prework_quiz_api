from django.urls import path
from .views import (
    StartAttemptView,
    AnswerView,
    SubmitAttemptView,
    ResumeAttemptView,
    AttemptHistoryView,
    SuspiciousEventView,
)

urlpatterns = [
    path("start/<uuid:quiz_id>/", StartAttemptView.as_view(), name="attempt-start"),
    path("<uuid:pk>/answer/", AnswerView.as_view(), name="attempt-answer"),
    path("<uuid:pk>/submit/", SubmitAttemptView.as_view(), name="attempt-submit"),
    path("<uuid:pk>/resume/", ResumeAttemptView.as_view(), name="attempt-resume"),
    path("<uuid:pk>/event/", SuspiciousEventView.as_view(), name="attempt-event"),
    path("history/", AttemptHistoryView.as_view(), name="attempt-history"),
]
