from django.urls import path

from . import views

app_name = "fitness"

urlpatterns = [
    # Renders the main HTML template
    path("", views.index, name="index"),

    # GET  /api/data/  — returns all log entries as JSON
    path("api/data/", views.get_fitness_data, name="fitness_data"),

    # POST /api/log/   — creates a new log entry
    path("api/log/", views.log_entry, name="log_entry"),
]
