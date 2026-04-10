from django.urls import include, path

from . import views

app_name = "fitness"

urlpatterns = [
    # Renders the main HTML template
    path("", views.index, name="index"),
    path('accounts/logout/', views.logout_view, name='logout'),
    path("api/data/", views.get_fitness_data, name="fitness_data"),
    path('accounts/', include('django.contrib.auth.urls')),
    path('signup/', views.signup, name='signup'),
    path("api/log/", views.log_entry, name="log_entry"),
]
