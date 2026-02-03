from django.contrib import admin
from django.contrib.auth.models import User
from django.contrib.auth.admin import UserAdmin
from django.utils.html import format_html, mark_safe
from django.shortcuts import redirect, get_object_or_404
from django.core.mail import send_mail
from django.conf import settings
from django.contrib import messages

from .models import (
    UserProfile, UserGoal, WorkoutPlan, DietPlan,
    UserWorkoutSession, UserDietRecord, BMIRecord
)
from .views import auto_assign_plan


# ================= USER PROFILE INLINE =================
class UserProfileInline(admin.StackedInline):
    model = UserProfile
    can_delete = False
    verbose_name_plural = "Profile"


# ================= WORKOUT & DIET INLINES =================
class UserWorkoutInline(admin.TabularInline):
    model = UserWorkoutSession
    extra = 0
    readonly_fields = (
        'workout_start', 'workout_end',
        'calories_burned', 'workout_plan'
    )
    can_delete = False


class UserDietInline(admin.TabularInline):
    model = UserDietRecord
    extra = 0
    readonly_fields = ('date', 'notes', 'diet_plan')
    can_delete = False


class UserGoalInline(admin.TabularInline):
    model = UserGoal
    extra = 0
    readonly_fields = (
        'current_weight', 'target_weight',
        'duration_days', 'diet_type',
        'status', 'workout_plan',
        'diet_plan', 'start_date'
    )
    can_delete = False


# ================= CUSTOM USER ADMIN =================
class CustomUserAdmin(UserAdmin):
    inlines = [
        UserProfileInline,
        UserGoalInline,
        UserWorkoutInline,
        UserDietInline
    ]
    list_display = (
        'username', 'email',
        'first_name', 'last_name',
        'is_staff'
    )
    search_fields = (
        'username', 'email',
        'first_name', 'last_name'
    )


admin.site.unregister(User)
admin.site.register(User, CustomUserAdmin)


# ================= SIMPLE ADMINS =================
admin.site.register(WorkoutPlan)
admin.site.register(DietPlan)
admin.site.register(BMIRecord)


# ================= USER GOAL ADMIN =================
@admin.register(UserGoal)
class UserGoalAdmin(admin.ModelAdmin):

    list_display = (
        "user",
        "current_weight",
        "target_weight",
        "colored_status",
        "start_date",
        "workout_plan",
        "diet_plan",
        "auto_assign_button",
    )

    list_filter = ("status", "diet_type")
    search_fields = ("user__username",)
    ordering = ("-start_date",)
    actions = ["approve_goals", "reject_goals"]


    # ---------- STATUS COLOR ----------
    def colored_status(self, obj):
        colors = {
            "pending": "orange",
            "approved": "green",
            "rejected": "red",
            "completed": "purple",
        }
        color = colors.get(obj.status.lower(), "black")
        return format_html(
            '<b style="color:{};">{}</b>',
            color, obj.status.capitalize()
        )
    colored_status.short_description = "Status"


    # ---------- AUTO ASSIGN BUTTON ----------
    def auto_assign_button(self, obj):
        if obj.status.lower() == "pending":
            return format_html(
                '<a class="button" '
                'style="background:#22c55e;color:white;'
                'padding:4px 10px;border-radius:6px;'
                'text-decoration:none;" '
                'href="auto_assign/{}/">Auto-Assign</a>',
                obj.id
            )
        return mark_safe('<span style="color:gray;">Assigned</span>')

    auto_assign_button.short_description = "Auto Assign"


    # ---------- ADMIN ACTIONS ----------
    def approve_goals(self, request, queryset):
        queryset.update(status="approved")
        for goal in queryset:
            self.notify_user(goal)
        self.message_user(request, "Selected goals approved.")

    def reject_goals(self, request, queryset):
        queryset.update(status="rejected")
        for goal in queryset:
            self.notify_user(goal)
        self.message_user(request, "Selected goals rejected.")


    # ---------- EMAIL NOTIFICATION ----------
    def notify_user(self, goal):
        if goal.user.email:
            send_mail(
                subject="Fitness Goal Update",
                message=(
                    f"Hello {goal.user.username},\n\n"
                    f"Your fitness goal status is now: {goal.status.capitalize()}.\n\n"
                    "Stay consistent!\nFitness Planner Team"
                ),
                from_email=settings.DEFAULT_FROM_EMAIL,
                recipient_list=[goal.user.email],
                fail_silently=True,
            )


    # ---------- CUSTOM ADMIN URL ----------
    def get_urls(self):
        from django.urls import path
        urls = super().get_urls()
        custom_urls = [
            path(
                "auto_assign/<int:goal_id>/",
                self.admin_site.admin_view(self.process_auto_assign),
                name="auto_assign_goal",
            ),
        ]
        return custom_urls + urls


    # ---------- AUTO ASSIGN LOGIC (SAFE) ----------
    def process_auto_assign(self, request, goal_id):
        goal = get_object_or_404(UserGoal, pk=goal_id)
        user = goal.user

        # 🔒 Ensure UserProfile exists
        UserProfile.objects.get_or_create(user=user)

        workout, diet = auto_assign_plan(user, goal)

        goal.workout_plan = workout
        goal.diet_plan = diet
        goal.status = "approved"
        goal.save()

        self.notify_user(goal)

        messages.success(
            request,
            f"Workout & Diet auto-assigned for {user.username}"
        )

        return redirect(request.META.get("HTTP_REFERER", "/admin/"))


    # ---------- SORTING ----------
    def get_queryset(self, request):
        qs = super().get_queryset(request)
        return qs.order_by("status", "-start_date")


# ================= ADMIN BRANDING =================
admin.site.site_header = "Fitness Planner Admin"
admin.site.site_title = "Fitness Planner"
admin.site.index_title = "Admin Dashboard"
