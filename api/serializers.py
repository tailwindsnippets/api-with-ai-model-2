# serializers.py
from rest_framework import serializers
from datetime import datetime
from .models import District, VulnerabilityIndex, NutrientAdequacy

class TextToSpeechSerializer(serializers.Serializer):
    VOICE_CHOICES = [
        ("alloy", "Alloy"),
        ("echo", "Echo"),
        ("fable", "Fable"),
        ("onyx", "Onyx"),
        ("nova", "Nova"),
        ("shimmer", "Shimmer"),
    ]

    text = serializers.CharField()
    voice = serializers.ChoiceField(choices=VOICE_CHOICES, default="alloy")
    name = serializers.CharField()
    webhook_url = serializers.URLField(required=False, allow_null=True, allow_blank=True)


class DistrictSerializer(serializers.ModelSerializer):
    class Meta:
        model = District
        fields = '__all__'


class VulnerabilityIndexSerializer(serializers.ModelSerializer):
    district = DistrictSerializer(read_only=True)
    district_id = serializers.PrimaryKeyRelatedField(
        queryset=District.objects.all(),
        source="district",
        write_only=True
    )

    class Meta:
        model = VulnerabilityIndex
        fields = ['id','name', 'district', 'district_id', 'code',
                  'category',
                  'value', 'color']


class NutrientAdequacySerializer(serializers.ModelSerializer):
    district = DistrictSerializer(read_only=True)
    district_id = serializers.PrimaryKeyRelatedField(
        queryset=District.objects.all(),
        source="district",
        write_only=True
    )

    class Meta:
        model = NutrientAdequacy
        fields = ['id', 'district', 'district_id', 'nutrient', 'value']

