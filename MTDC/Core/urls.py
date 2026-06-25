from django.urls import path
from django.contrib.auth import views as auth_views

from . import views

app_name = 'core'

urlpatterns = [
    path(
        'login/',
        auth_views.LoginView.as_view(
            template_name='login.html',
            redirect_authenticated_user=True,
        ),
        name='login',
    ),
    path(
        'logout/',
        auth_views.LogoutView.as_view(next_page='core:login'),
        name='logout',
    ),
    path('', views.dashboard, name='dashboard'),
    path('analytics/', views.analytics, name='analytics'),
    path('property/<int:property_id>/', views.dashboard, name='property_detail'),
]
