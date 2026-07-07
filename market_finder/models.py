from django.db import models

class MandiLocation(models.Model):
    market_name = models.CharField(max_length=255)
    district = models.CharField(max_length=255)
    state = models.CharField(max_length=100, default="Gujarat")
    latitude = models.FloatField()
    longitude = models.FloatField()

    class Meta:
        unique_together = ('market_name', 'district')

    def __str__(self):
        return f"{self.market_name}, {self.district}"