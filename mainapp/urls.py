from django.urls import path
from . import views

urlpatterns = [
    path('', views.dashboard, name='dashboard'),
    path('weight-gain/', views.weight_gain, name='weight_gain'),
    path('weight-loss/', views.weight_loss, name='weight_loss'),
    path('contact/', views.contact, name='contact'),
    path('know-more/', views.know_more, name='know_more'),
    path('login/', views.login_view, name='login'),
    path('register/', views.register, name='register'),
    path('profile/', views.profile, name='profile'),
    path('logout/', views.logout_view, name='logout'),
    path('bmi/', views.bmi_view, name='bmi'),
    path('body-fat/', views.body_fat_view, name='body_fat'),
]
