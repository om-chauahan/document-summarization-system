from django.urls import path
from . import views

urlpatterns = [
    path('api/summarize/', views.summarize_document, name='summarize_document'),
]

