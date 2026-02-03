# mainapp/scripts/populate_workoutplans.py
import os
import django

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "fitnessplanner.settings")
django.setup()

from mainapp.models import WorkoutPlan

plans = [
    WorkoutPlan(
        title="Gain Beginner 1", plan_type="gain", level="beginner",
        workout_description="3x per week: Squats, Bench Press, Deadlift, Pull-ups, Core exercises"
    ),
    WorkoutPlan(
        title="Gain Intermediate 1", plan_type="gain", level="intermediate",
        workout_description="4x per week: Compound lifts + accessory exercises for arms, chest, back"
    ),
    WorkoutPlan(
        title="Loss Beginner 1", plan_type="loss", level="beginner",
        workout_description="3x per week: Cardio 30min, Bodyweight exercises, Core"
    ),
    WorkoutPlan(
        title="Loss Intermediate 1", plan_type="loss", level="intermediate",
        workout_description="4x per week: HIIT 20min, Strength circuits, Cardio 20min"
    ),
]

WorkoutPlan.objects.bulk_create(plans)
print("✅ Workout plans populated successfully!")

