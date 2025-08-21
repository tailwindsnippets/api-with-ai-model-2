from django.urls import path, include
from .views import TextToSpeechAPIView, TaskStatusAPIView, generate_prompts
from .views import GenerateImageView
from api.views import CreateVideoFromImagesView
from rest_framework.routers import DefaultRouter
from api.views import DistrictViewSet, VulnerabilityIndexViewSet, NutrientAdequacyViewSet
from .views import predict_view

router = DefaultRouter()

router.register(r'districts', DistrictViewSet)
router.register(r'vulnerability', VulnerabilityIndexViewSet)
router.register(r'nutrients', NutrientAdequacyViewSet)

urlpatterns = [
    path('me/', include(router.urls)),
     path('predict/', predict_view, name='predict-nutrients'),
    path("text-to-speech/", TextToSpeechAPIView.as_view(), name="text-to-speech"),
    path("task-status/<str:task_id>/", TaskStatusAPIView.as_view(), name="task-status"),
    path("generate-prompts/", generate_prompts, name="generate_prompts"),
    path("generate-image/", GenerateImageView.as_view(), name="generate_image"),
    path("create-video/", CreateVideoFromImagesView.as_view(), name="create-video"),
]