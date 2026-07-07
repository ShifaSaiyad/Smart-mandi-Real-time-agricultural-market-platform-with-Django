from django.db import models


class AboutContent(models.Model):
    title = models.CharField(max_length=200, default="About Smart Mandi")
    hero_text = models.TextField()
    mission = models.TextField()
    vision = models.TextField()
    highlight_one = models.CharField(max_length=255)
    highlight_two = models.CharField(max_length=255)
    highlight_three = models.CharField(max_length=255)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.title

# Create your models here.
