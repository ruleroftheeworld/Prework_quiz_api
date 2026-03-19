from django.urls import path
from .views import QuizListCreateView, QuizDetailView

urlpatterns = [
    path("", QuizListCreateView.as_view(), name="quiz-list-create"),
    path("<uuid:pk>/", QuizDetailView.as_view(), name="quiz-detail"),
]
