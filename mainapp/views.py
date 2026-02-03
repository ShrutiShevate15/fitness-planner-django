from datetime import date, timedelta

from django.shortcuts import render, redirect
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required
from django.contrib.admin.views.decorators import staff_member_required
from django.contrib import messages
from django.core.mail import send_mail
from django.conf import settings

from .forms import (
    WeightGainForm, WeightLossForm, CustomUserCreationForm
)
from .models import (
    UserProfile, UserGoal, WorkoutPlan, DietPlan, BMIRecord
)
from .utils import get_bmi_category


# -----------------------------
# DASHBOARD
# -----------------------------
@login_required
def dashboard(request):
    profile = UserProfile.objects.filter(user=request.user).first()

    latest_bmi = 22
    latest_body_fat = None
    chart_labels, bmi_data, body_fat_data = [], [], []
    bmi_trend, body_fat_trend = 'same', 'same'

    age = profile.age if profile and profile.age else 25
    gender = 1 if profile and profile.gender == 'male' else 0

    entries = list(
        BMIRecord.objects.filter(user=request.user).order_by('-id')[:7][::-1]
    )
    valid_entries = [e for e in entries if e.bmi is not None]

    if valid_entries:
        latest_bmi = valid_entries[-1].bmi
        latest_body_fat = round(
            (1.20 * latest_bmi) + (0.23 * age) - (10.8 * gender) - 5.4, 2
        )

        if len(valid_entries) > 1:
            prev_bmi = valid_entries[-2].bmi
            prev_body_fat = round(
                (1.20 * prev_bmi) + (0.23 * age) - (10.8 * gender) - 5.4, 2
            )
            bmi_trend = 'up' if latest_bmi > prev_bmi else 'down' if latest_bmi < prev_bmi else 'same'
            body_fat_trend = 'up' if latest_body_fat > prev_body_fat else 'down' if latest_body_fat < prev_body_fat else 'same'

        for e in valid_entries:
            chart_labels.append(
                e.created_at.strftime("%d %b") if hasattr(e, 'created_at') else ""
            )
            bmi_data.append(e.bmi)
            body_fat_data.append(
                round((1.20 * e.bmi) + (0.23 * age) - (10.8 * gender) - 5.4, 2)
            )
    else:
        latest_body_fat = round(
            (1.20 * latest_bmi) + (0.23 * age) - (10.8 * gender) - 5.4, 2
        )

    return render(request, "dashboard.html", {
        "latest_bmi": latest_bmi,
        "latest_body_fat": latest_body_fat,
        "bmi_trend": bmi_trend,
        "body_fat_trend": body_fat_trend,
        "chart_labels": chart_labels,
        "bmi_data": bmi_data,
        "body_fat_data": body_fat_data,
    })


# -----------------------------
# AUTO ASSIGN PLAN
# -----------------------------
def auto_assign_plan(user, goal):
    profile = user.userprofile
    bmi_record = BMIRecord.objects.filter(user=user).order_by('-id').first()
    bmi = bmi_record.bmi if bmi_record else 22

    age = profile.age or 25
    diet_pref = profile.diet_preference
    bmi_category = get_bmi_category(bmi)

    is_loss = goal.target_weight and goal.target_weight < goal.current_weight
    goal_type = 'loss' if is_loss else 'gain'
    workout_level = 'beginner' if age > 45 or bmi_category in ['obese', 'overweight'] else 'intermediate'

    workout = WorkoutPlan.objects.filter(
        plan_type=goal_type, level=workout_level
    ).first()
    diet = DietPlan.objects.filter(
        plan_type=goal_type, diet_type=diet_pref
    ).first()

    return workout, diet


from datetime import date, timedelta
from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from django.contrib import messages

from .models import UserProfile, UserGoal, WorkoutPlan, DietPlan
from .forms import WeightGainForm

# -----------------------------
# WEIGHT GAIN VIEW
# -----------------------------
@login_required
def weight_gain(request):
    user = request.user
    profile = UserProfile.objects.filter(user=user).first()

    # Get the latest assigned goal
    existing_goal = UserGoal.objects.filter(user=user, status='assigned').order_by('-id').first()

    if existing_goal:
        # Get workout and diet plans for weight gain
        workouts = WorkoutPlan.objects.filter(plan_type='gain')
        diets = DietPlan.objects.filter(plan_type='gain', diet_type=existing_goal.diet_type)

        # Build daily schedule
        schedule = []
        start_date = existing_goal.start_date or date.today()
        duration_days = existing_goal.duration_days or 30

        for i in range(duration_days):
            day_date = start_date + timedelta(days=i)
            is_workout = i % 2 == 0
            schedule.append({
                "date": day_date,
                "is_workout": is_workout,
                "workout": workouts.first() if is_workout and workouts.exists() else None,
                "meals": diets[:2] if diets.exists() else []
            })

        return render(
            request,
            "weight_gain_plan.html",
            {
                "goal": existing_goal,
                "schedule": schedule,
                "workouts": workouts if workouts.exists() else [],
                "diets": diets if diets.exists() else [],
                "profile": profile
            }
        )

    # Handle form submission
    if request.method == "POST":
        form = WeightGainForm(request.POST)
        if form.is_valid():
            # Update or create profile
            UserProfile.objects.update_or_create(
                user=user,
                defaults={
                    "height_cm": form.cleaned_data.get("height_cm") or 0,
                    "weight_kg": form.cleaned_data.get("current_weight") or 0,
                    "goal": "gain"
                }
            )

            # Create pending goal
            UserGoal.objects.create(
                user=user,
                current_weight=form.cleaned_data.get("current_weight") or 0,
                target_weight=form.cleaned_data.get("target_gain") or 0,
                duration_days=form.cleaned_data.get("duration_days") or 0,
                diet_type=form.cleaned_data.get("diet_type"),
                status='pending'
            )

            messages.success(
                request,
                "Weight gain goal submitted! Admin will assign your plan soon."
            )
            return redirect("weight_gain")
    else:
        form = WeightGainForm()

    return render(
        request,
        "weight_gain_form.html",
        {"form": form, "profile": profile}
    )


from datetime import date, timedelta
from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from django.contrib import messages

from .models import UserProfile, UserGoal, WorkoutPlan, DietPlan
from .forms import WeightLossForm

# -----------------------------
# WEIGHT LOSS VIEW
# -----------------------------
@login_required
def weight_loss(request):
    user = request.user
    profile = UserProfile.objects.filter(user=user).first()
    
    # Get the latest assigned goal
    existing_goal = UserGoal.objects.filter(user=user, status='assigned').order_by('-id').first()

    if existing_goal:
        # Get workout and diet plans for weight loss
        workouts = WorkoutPlan.objects.filter(plan_type='loss')
        diets = DietPlan.objects.filter(plan_type='loss', diet_type=existing_goal.diet_type)

        # Build daily schedule
        schedule = []
        start_date = existing_goal.start_date or date.today()
        duration_days = existing_goal.duration_days or 30

        for i in range(duration_days):
            day_date = start_date + timedelta(days=i)
            is_workout = i % 2 == 0
            schedule.append({
                "date": day_date,
                "is_workout": is_workout,
                "workout": workouts.first() if is_workout and workouts.exists() else None,
                "meals": diets[:2] if diets.exists() else []
            })

        return render(
            request,
            "weight_loss_plan.html",
            {
                "goal": existing_goal,
                "schedule": schedule,
                "workouts": workouts if workouts.exists() else [],
                "diets": diets if diets.exists() else [],
                "profile": profile
            }
        )

    # Handle form submission
    if request.method == "POST":
        form = WeightLossForm(request.POST)
        if form.is_valid():
            UserGoal.objects.create(
                user=user,
                current_weight=form.cleaned_data['current_weight'],
                target_weight=form.cleaned_data['target_weight'],
                duration_days=form.cleaned_data['duration_days'],
                diet_type=form.cleaned_data['diet_type'],
                status='pending'
            )
            messages.success(request, "Weight loss goal submitted! Admin will assign your plan soon.")
            return redirect("weight_loss")
    else:
        form = WeightLossForm()

    return render(
        request,
        "weight_loss_form.html",
        {"form": form, "profile": profile}
    )


# -----------------------------
# PROFILE
# -----------------------------
@login_required
def profile(request):
    user = request.user
    profile = UserProfile.objects.filter(user=user).first()
    goal = UserGoal.objects.filter(user=user).order_by('-id').first()

    diet_plan = workout_plan = None
    progress = 0

    if goal:
        is_loss = goal.target_weight and goal.target_weight < goal.current_weight
        plan_type = 'loss' if is_loss else 'gain'

        diet_plan = DietPlan.objects.filter(
            plan_type=plan_type, diet_type=goal.diet_type
        ).first()
        workout_plan = WorkoutPlan.objects.filter(
            plan_type=plan_type
        ).first()

        if goal.current_weight and goal.target_weight:
            progress = 50  # placeholder

    return render(request, "profile.html", {
        "profile": profile,
        "goal": goal,
        "diet_plan": diet_plan,
        "workout_plan": workout_plan,
        "progress": int(progress),
    })


# -----------------------------
# AUTH
# -----------------------------
def login_view(request):
    if request.method == "POST":
        username = request.POST.get("username")
        password = request.POST.get("password")
        user = authenticate(request, username=username, password=password)

        if user:
            login(request, user)
            messages.success(request, f"Welcome back, {username}!")
            return redirect("dashboard")
        messages.error(request, "Invalid username or password")

    return render(request, "login.html")


@login_required
def logout_view(request):
    logout(request)
    messages.success(request, "You have been logged out.")
    return redirect("login")


from django.shortcuts import render, redirect
from django.contrib.auth import login
from django.contrib import messages
from .forms import CustomUserCreationForm

def register(request):
    if request.method == 'POST':
        form = CustomUserCreationForm(request.POST)
        if form.is_valid():
            user = form.save()
            login(request, user)

            # Update UserProfile created by signal
            profile = user.userprofile
            profile.age = form.cleaned_data.get('age')
            profile.gender = form.cleaned_data.get('gender')
            profile.diet_preference = form.cleaned_data.get('diet_preference')
            profile.save()

            messages.success(request, "Account created successfully!")
            return redirect('dashboard')
        else:
            messages.error(request, "Please correct the errors below.")
    else:
        form = CustomUserCreationForm()

    return render(request, 'register.html', {'form': form})



# -----------------------------
# STATIC PAGES
# -----------------------------
def contact(request):
    return render(request, "contact.html")


def know_more(request):
    return render(request, "know_more.html")


# -----------------------------
# BMI & BODY FAT
# -----------------------------
@login_required
def bmi_view(request):
    bmi = category = None

    if request.method == "POST":
        try:
            weight = float(request.POST.get("weight") or 0)
            height_cm = float(request.POST.get("height") or 0)

            if height_cm > 0:
                height_m = height_cm / 100
                bmi = round(weight / (height_m ** 2), 2)
                category = (
                    "Underweight" if bmi < 18.5 else
                    "Normal" if bmi < 25 else
                    "Overweight" if bmi < 30 else
                    "Obese"
                )

                BMIRecord.objects.create(
                    user=request.user,
                    weight_kg=weight,
                    height_cm=height_cm,
                    bmi=bmi,
                    category=category
                )

                UserProfile.objects.update_or_create(
                    user=request.user,
                    defaults={"height_cm": height_cm, "weight_kg": weight}
                )
            else:
                messages.error(request, "Height must be greater than zero")
        except:
            messages.error(request, "Please enter valid values")

    return render(request, "bmi.html", {"bmi": bmi, "category": category})


@login_required
def body_fat_view(request):
    body_fat = None

    if request.method == "POST":
        try:
            height = float(request.POST.get("height") or 0)
            weight = float(request.POST.get("weight") or 0)
            age = int(request.POST.get("age") or 25)
            gender = int(request.POST.get("gender") or 1)

            if height > 0:
                height_m = height / 100
                bmi = weight / (height_m ** 2)
                body_fat = round(
                    (1.20 * bmi) + (0.23 * age) - (10.8 * gender) - 5.4, 2
                )
            else:
                messages.error(request, "Height must be greater than zero")
        except:
            messages.error(request, "Please enter valid values")

    return render(request, "body_fat.html", {"body_fat": body_fat})


# -----------------------------
# ADMIN GOAL DASHBOARD
# -----------------------------
@staff_member_required
def goal_dashboard(request):
    pending_goals = UserGoal.objects.filter(
        status__iexact="pending"
    ).order_by("-start_date")

    if request.method == "POST":
        goal_id = request.POST.get("goal_id")
        action = request.POST.get("action")
        goal = UserGoal.objects.get(id=goal_id)

        if action == "approve":
            goal.status = "approved"
        elif action == "reject":
            goal.status = "rejected"
        elif action == "auto_assign":
            workout, diet = auto_assign_plan(goal.user, goal)
            goal.workout_plan = workout
            goal.diet_plan = diet
            goal.status = "approved"

        goal.save()

        if goal.user.email:
            send_mail(
                subject="Your Fitness Goal Status",
                message=f"Hello {goal.user.username}, your goal is now {goal.status}.",
                from_email=settings.DEFAULT_FROM_EMAIL,
                recipient_list=[goal.user.email],
                fail_silently=True,
            )

        messages.success(
            request,
            f"Goal for {goal.user.username} updated to {goal.status}!"
        )
        return redirect("goal_dashboard")

    return render(
        request,
        "mainapp/goal_dashboard.html",
        {"pending_goals": pending_goals}
    )


from datetime import timedelta
from django.shortcuts import render, get_object_or_404
from .models import UserGoal, DietDay, WorkoutDay

@login_required
def user_plan_view(request):
    goal = get_object_or_404(UserGoal, user=request.user, status='assigned')

    diet_days = DietDay.objects.filter(plan=goal.diet_plan).order_by('day_number') if goal.diet_plan else []
    workout_days = WorkoutDay.objects.filter(plan=goal.workout_plan).order_by('day_number') if goal.workout_plan else []

    days = []
    for i in range(goal.duration_days):
        day_number = i + 1
        days.append({
            'day_number': day_number,
            'date': goal.start_date + timedelta(days=i),
            'diet': next((d for d in diet_days if d.day_number == day_number), None),
            'workout': next((w for w in workout_days if w.day_number == day_number), None),
        })

    return render(request, 'user_plan.html', {
        'goal': goal,
        'days': days
    })
