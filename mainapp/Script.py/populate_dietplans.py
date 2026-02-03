# mainapp/scripts/populate_dietplans.py
import os
import django

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "fitnessplanner.settings")
django.setup()

from mainapp.models import DietPlan

# Create sample diet plans
plans = [
    DietPlan(
        title="Gain Plan 1", plan_type="gain", diet_type="veg", calories=3000,
        meals="Breakfast: Oats + Milk + Banana\nSnack: Nuts + Yogurt\nLunch: Rice + Dal + Paneer + Veg\nSnack: Smoothie\nDinner: Chapati + Lentils + Veg"
    ),
    DietPlan(
        title="Gain Plan 2", plan_type="gain", diet_type="nonveg", calories=3200,
        meals="Breakfast: Eggs + Toast + Milk\nSnack: Protein Shake + Nuts\nLunch: Chicken + Rice + Veg\nSnack: Peanut Butter Sandwich\nDinner: Fish + Quinoa + Veg"
    ),
    DietPlan(
        title="Loss Plan 1", plan_type="loss", diet_type="veg", calories=1800,
        meals="Breakfast: Oats + Berries\nSnack: Fruit\nLunch: Salad + Lentils\nSnack: Yogurt\nDinner: Soup + Veg"
    ),
    DietPlan(
        title="Loss Plan 2", plan_type="loss", diet_type="nonveg", calories=2000,
        meals="Breakfast: Eggs + Veg\nSnack: Protein Shake\nLunch: Chicken + Salad\nSnack: Fruit\nDinner: Fish + Veg"
    ),
]

DietPlan.objects.bulk_create(plans)
print("✅ Diet plans populated successfully!")
