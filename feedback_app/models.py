from django.db import models


class Feedback(models.Model):
    RATING_CHOICES = [(value, f"{value} Star") for value in range(1, 6)]

    name = models.CharField(max_length=150)
    email = models.EmailField()
    rating = models.PositiveSmallIntegerField(choices=RATING_CHOICES)
    message = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.name} - {self.rating}"

# Create your models here.
