from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from .serializers import TextToSpeechSerializer
from .tasks import generate_audio_and_srt
from celery.result import AsyncResult
from rest_framework.decorators import api_view
from rest_framework.response import Response
from .tasks import generate_prompts_from_srt_url
from .models import VisualPrompt
from .tasks import generate_image_from_prompt
#openai.api_key = "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"
from api.tasks import create_video_from_images
from .models import District, VulnerabilityIndex, NutrientAdequacy
from .serializers import DistrictSerializer, VulnerabilityIndexSerializer, NutrientAdequacySerializer
from rest_framework import viewsets


import pandas as pd
from joblib import load
from rest_framework.decorators import api_view
from rest_framework.response import Response
from rest_framework import status

# Load the trained model once
model = load("malawi_nutrient_model.joblib")

# Baseline nutrient values
DEFAULT_BASELINE = {
    "baseline_Kilocalories_kcal": 84.88,
    "baseline_Proteins_g": 95.99,
    "baseline_Iron_mg": 98.25,
    "baseline_Calcium_mg": 92.71,
    "baseline_Folate_mcg": 81.42,
    "baseline_Niacin_mg": 68.17,
    "baseline_Riboflavin_mg": 52.47,
    "baseline_Thiamin_mg": 93.35,
    "baseline_VitaminA_mcg": 54.48,
    "baseline_VitaminB6_mg": 90.68,
    "baseline_VitaminB12_mcg": 22.9,
    "baseline_VitaminC_mg": 90.87,
    "baseline_Zinc_mg": 88.63,
}
BASELINE_DATA = [92.71, 81.42, 98.25, 84.88, 68.17, 95.99, 52.47, 93.35, 54.48, 22.9, 90.68, 90.87, 88.63]

# Map nutrients to baseline columns
NUTRIENT_COLUMNS = {
    "Calcium": "baseline_Calcium_mg",
    "Folate": "baseline_Folate_mcg",
    "Iron": "baseline_Iron_mg",
    "Kilocalories": "baseline_Kilocalories_kcal",
    "Niacin": "baseline_Niacin_mg",
    "Proteins": "baseline_Proteins_g",
    "Riboflavin": "baseline_Riboflavin_mg",
    "Thiamin": "baseline_Thiamin_mg",
    "Vitamin A": "baseline_VitaminA_mcg",
    "Vitamin B12": "baseline_VitaminB12_mcg",
    "Vitamin B6": "baseline_VitaminB6_mg",
    "Vitamin C": "baseline_VitaminC_mg",
    "Zinc": "baseline_Zinc_mg",
}

# Food group nutrient mapping
FOOD_GROUP_NUTRIENTS = {
    "All": list(NUTRIENT_COLUMNS.keys()),
    "Beverages": ["Kilocalories", "Vitamin C"],
    "Cereals, Grains and Cereal Products": ["Kilocalories", "Proteins", "Thiamin", "Niacin", "Riboflavin", "Iron", "Folate"],
    "Cooked Foods from Vendors": ["Kilocalories", "Proteins"],
    "Fruits": ["Vitamin C", "Vitamin A", "Folate", "Kilocalories"],
    "Meat, Fish and Animal products": ["Proteins", "Vitamin B12", "Iron", "Zinc", "Niacin", "Riboflavin", "Thiamin"],
    "Milk and Milk Products": ["Calcium", "Proteins", "Vitamin B12", "Riboflavin", "Kilocalories"],
    "Nuts and Pulses": ["Proteins", "Iron", "Zinc", "Niacin", "Folate", "Kilocalories"],
    "Oils and Fats": ["Kilocalories", "Vitamin A"],
    "Roots, Tubers, and Plantains": ["Kilocalories", "Vitamin C", "Folate"],
    "Spices and Miscellaneous": ["Vitamin A", "Vitamin C"],
    "Sugar and sweet": ["Kilocalories"],
    "Vegetables": ["Vitamin A", "Vitamin C", "Folate", "Kilocalories"]
}

def predict_nutrients(location, food_group, percentage_change, baseline_data_values=None):
    if baseline_data_values is None:
        baseline_data_values = {}
    features = DEFAULT_BASELINE.copy()
    features.update(baseline_data_values)

    affected_nutrients = FOOD_GROUP_NUTRIENTS.get(food_group, [])
    for nutrient in affected_nutrients:
        col_name = NUTRIENT_COLUMNS.get(nutrient)
        if col_name and col_name in features:
            features[col_name] = features[col_name] * (1 - int(percentage_change) / 100.0)

    data = {
        "district": [location],
        "food_group": [food_group],
        "simulation": [percentage_change],
        **{k: [v] for k, v in features.items()}
    }
    X_new = pd.DataFrame(data)
    prediction = model.predict(X_new)
    return {"intervention_pred": prediction[0].tolist(), "baseline_pred": BASELINE_DATA}

# --- Django view ---
@api_view(['POST'])
def predict_view(request):
    """
    POST JSON example:
    {
        "location": "Lilongwe",
        "food_group": "Fruits",
        "percentage_change": 90
    }
    """
    data = request.data
    location = data.get("location")
    food_group = data.get("food_group")
    percentage_change = data.get("percentage_change")

    if not location or not food_group or percentage_change is None:
        return Response({"error": "location, food_group, and percentage_change are required."},
                        status=status.HTTP_400_BAD_REQUEST)

    result = predict_nutrients(location, food_group, percentage_change)
    return Response(result)



class DistrictViewSet(viewsets.ModelViewSet):
    queryset = District.objects.all()
    serializer_class = DistrictSerializer


class VulnerabilityIndexViewSet(viewsets.ModelViewSet):
    queryset = VulnerabilityIndex.objects.all()
    serializer_class = VulnerabilityIndexSerializer


class NutrientAdequacyViewSet(viewsets.ModelViewSet):
    queryset = NutrientAdequacy.objects.all()
    serializer_class = NutrientAdequacySerializer


class TextToSpeechAPIView(APIView):
    def post(self, request):
        serializer = TextToSpeechSerializer(data=request.data)
        if serializer.is_valid():
            text = serializer.validated_data["text"]
            voice = serializer.validated_data["voice"]
            name = serializer.validated_data["name"]
            webhook_url = serializer.validated_data["webhook_url"]
            task = generate_audio_and_srt.delay(text, voice, name, webhook_url)

            return Response({
                "success": True,
                "task_id": task.id
            }, status=status.HTTP_202_ACCEPTED)

        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    

class TaskStatusAPIView(APIView):
    def get(self, request, task_id):
        result = AsyncResult(task_id)
        data = {
            "task_id": task_id,
            "status": result.status,
            "result": result.result if result.ready() else None,
        }
        return Response(data)
    

@api_view(["POST"])
def generate_prompts(request):
    srt_url = request.data.get("srt_url")
    webhook_url = request.data.get("webhook_url")
    if not srt_url:
        return Response({"error": "Missing 'srt_url' in request."}, status=400)
    
    task = generate_prompts_from_srt_url.delay(srt_url, webhook_url)
    return Response({"message": "Processing started.", "task_id": task.id})


class GenerateImageView(APIView):
    def post(self, request):
        prompt = request.data.get("prompt")
        start = request.data.get("start", "")
        end = request.data.get("end", "")
        webhook_url = request.data.get("webhook_url")

        if not prompt:
            return Response({"error": "Prompt is required."}, status=status.HTTP_400_BAD_REQUEST)

        # Save to DB
        prompt_obj = VisualPrompt.objects.create(prompt=prompt, start=start, end=end)

        # Trigger Celery task
        task= generate_image_from_prompt.delay(prompt_obj.id, webhook_url)

        return Response(
            {"message": "Image generation task started.", "task_id": task.id},
            status=status.HTTP_202_ACCEPTED
        )

class CreateVideoFromImagesView(APIView):
    def post(self, request):
        mp3_url = request.data.get("mp3_url")
        images = request.data.get("images")
        webhook_url = request.data.get("webhook_url")

        if not mp3_url or not images:
            return Response({"error": "mp3_url and images are required"}, status=400)

        task = create_video_from_images.delay(mp3_url, images, webhook_url)
        return Response({"task_id": task.id}, status=status.HTTP_202_ACCEPTED)