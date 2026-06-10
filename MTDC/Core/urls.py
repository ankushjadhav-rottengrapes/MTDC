from django.urls import path

from . import views

app_name = 'core'

urlpatterns = [
    path('', views.dashboard, name='dashboard'),
    path('property/<int:property_id>/', views.dashboard, name='property_detail'),
]
