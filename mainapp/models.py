from django.db import models
from django.conf import settings
from django.contrib.auth.models import User

# ========================= BMI RECORD =========================
class BMIRecord(models.Model):
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        null=True,
        blank=True,
        on_delete=models.SET_NULL
    )
    weight_kg = models.FloatField()
    height_cm = models.FloatField()
    bmi = models.FloatField()
    category = models.CharField(max_length=50)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.bmi:.2f} ({self.category})"


# ========================= USER PROFILE =========================
class UserProfile(models.Model):
    DIET_CHOICES = [
        ('veg', 'Vegetarian'),
        ('nonveg', 'Non-Vegetarian'),
        ('vegan', 'Vegan'),
    ]

    GENDER_CHOICES = [
        ('male', 'Male'),
        ('female', 'Female'),
    ]

    user = models.OneToOneField(User, on_delete=models.CASCADE)
    age = models.IntegerField(null=True, blank=True)
    gender = models.CharField(max_length=10, choices=GENDER_CHOICES, null=True, blank=True)
    height_cm = models.FloatField(null=True, blank=True)
    weight_kg = models.FloatField(null=True, blank=True)
    diet_preference = models.CharField(max_length=20, choices=DIET_CHOICES, default='veg')
    medical_issue = models.TextField(null=True, blank=True)

    def __str__(self):
        return self.user.username


# ========================= DIET PLAN =========================
class DietPlan(models.Model):
    PLAN_TYPE = [
        ('gain', 'Weight Gain'),
        ('loss', 'Weight Loss'),
    ]
    DIET_CHOICES = [
        ('veg', 'Vegetarian'),
        ('nonveg', 'Non-Vegetarian'),
        ('vegan', 'Vegan'),
    ]

    title = models.CharField(max_length=200)
    plan_type = models.CharField(max_length=10, choices=PLAN_TYPE)
    diet_type = models.CharField(max_length=10, choices=DIET_CHOICES)
    calories = models.IntegerField()
    meals = models.TextField(help_text="Breakfast, lunch, dinner")
    medical_issue_suitable = models.TextField(null=True, blank=True)

    def __str__(self):
        return self.title


# ========================= WORKOUT PLAN =========================
class WorkoutPlan(models.Model):
    PLAN_TYPE = [
        ('gain', 'Weight Gain'),
        ('loss', 'Weight Loss'),
    ]
    LEVEL_CHOICES = [
        ('beginner', 'Beginner'),
        ('intermediate', 'Intermediate'),
        ('advanced', 'Advanced'),
    ]

    title = models.CharField(max_length=200)
    plan_type = models.CharField(max_length=10, choices=PLAN_TYPE)
    level = models.CharField(max_length=20, choices=LEVEL_CHOICES)
    workout_description = models.TextField()

    def __str__(self):
        return self.title


# ========================= USER GOAL =========================
from django.db import models
from django.contrib.auth.models import User

class UserGoal(models.Model):
    DIET_CHOICES = [
        ('veg', 'Vegetarian'),
        ('nonveg', 'Non-Vegetarian'),
        ('vegan', 'Vegan'),
    ]
    STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('assigned', 'Assigned'),
        ('completed', 'Completed'),
    ]

    user = models.ForeignKey(User, on_delete=models.CASCADE)
    current_weight = models.FloatField(null=True, blank=True)
    target_weight = models.FloatField(null=True, blank=True)
    duration_days = models.IntegerField(null=True, blank=True)
    diet_type = models.CharField(max_length=10, choices=DIET_CHOICES, null=True, blank=True)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    start_date = models.DateField(auto_now_add=True)

    # New fields to store assigned plans
    workout_plan = models.ForeignKey(
        'WorkoutPlan', on_delete=models.SET_NULL, null=True, blank=True
    )
    diet_plan = models.ForeignKey(
        'DietPlan', on_delete=models.SET_NULL, null=True, blank=True
    )

    def __str__(self):
        return f"{self.user.username} - Goal"

    # Dynamic property to infer gain or loss
    @property
    def goal_type(self):
        if self.current_weight and self.target_weight:
            return 'gain' if self.target_weight > self.current_weight else 'loss'
        return None


# ========================= WORKOUT SESSION =========================
class UserWorkoutSession(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    workout_plan = models.ForeignKey(
        WorkoutPlan, on_delete=models.SET_NULL, null=True
    )
    workout_start = models.DateTimeField()
    workout_end = models.DateTimeField()
    calories_burned = models.FloatField(null=True, blank=True)

    def __str__(self):
        return f"{self.user.username} - {self.workout_start.date()}"


# ========================= USER DIET RECORD =========================
class UserDietRecord(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    diet_plan = models.ForeignKey(
        DietPlan, on_delete=models.SET_NULL, null=True
    )
    date = models.DateField(auto_now_add=True)
    notes = models.TextField(blank=True, null=True)

    def __str__(self):
        return f"{self.user.username} - {self.date}"

# ========================= DAILY DIET =========================
class DietDay(models.Model):
    plan = models.ForeignKey(DietPlan, on_delete=models.CASCADE)
    day_number = models.IntegerField()
    breakfast = models.TextField()
    mid_morning_snack = models.TextField()
    lunch = models.TextField()
    evening_snack = models.TextField()
    dinner = models.TextField()

    class Meta:
        unique_together = ('plan', 'day_number')
        ordering = ['day_number']

    def __str__(self):
        return f"{self.plan.title} - Day {self.day_number}"


# ========================= DAILY WORKOUT =========================
class WorkoutDay(models.Model):
    plan = models.ForeignKey(WorkoutPlan, on_delete=models.CASCADE)
    day_number = models.IntegerField()
    exercises = models.TextField()

    class Meta:
        unique_together = ('plan', 'day_number')
        ordering = ['day_number']

    def __str__(self):
        return f"{self.plan.title} - Day {self.day_number}"
