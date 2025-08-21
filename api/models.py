from django.db import models

class VisualPrompt(models.Model):
    start = models.CharField(max_length=20)
    end = models.CharField(max_length=20)
    prompt = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)


class GeneratedImage(models.Model):
    prompt = models.ForeignKey(VisualPrompt, on_delete=models.CASCADE, related_name="images")
    image_url = models.URLField()
    created_at = models.DateTimeField(auto_now_add=True)


class District(models.Model):
    name = models.CharField(max_length=100, unique=True)

    def __str__(self):
        return self.name




class VulnerabilityIndex(models.Model):
    name = models.CharField(max_length=150, default="Composite Vulnerability Index")
    code = models.CharField(max_length=50, default="cv_index")
    district = models.ForeignKey(District, on_delete=models.CASCADE, related_name="cv_indexes")
    value = models.FloatField()
    category = models.CharField(max_length=100)
    color = models.CharField(max_length=20)

    def __str__(self):
        return f"{self.district.name} - {self.value}"


class NutrientAdequacy(models.Model):
    district = models.ForeignKey(District, on_delete=models.CASCADE, related_name="nutrient_adequacies")
    nutrient = models.CharField(max_length=100)  # e.g. Iron, Vitamin A, etc.
    value = models.FloatField()  # adequacy percentage

    def __str__(self):
        return f"{self.district.name} - {self.nutrient}"