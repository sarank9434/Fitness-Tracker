from django.db import models

class FatLossLog(models.Model):
    date = models.DateField(auto_now_add=True)
    goal_completion = models.BooleanField(default=False)
    weight = models.FloatField(help_text="Weight in kg")
    waist_size = models.FloatField(help_text="Waist size in inches")
    thigh_size = models.FloatField(help_text="Thigh size in inches")
    
    # BMI is usually a calculated value, so we use a property 
    # rather than saving it to the database to avoid data redundancy.
    @property
    def bmi(self):
        # Assuming height is constant for now. 
        # Formula: weight (kg) / [height (m)]^2
        # Replace 1.65 with your actual height in meters.
        height_m = 1.65 
        return round(self.weight / (height_m ** 2), 1)

    def __str__(self):
        return f"Log for {self.date} - Weight: {self.weight}"

    class Meta:
        ordering = ['-date']