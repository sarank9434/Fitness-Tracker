import json
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from django.middleware.csrf import get_token
from django.shortcuts import render
from django.urls import reverse
from .models import FatLossLog
from django.contrib.auth.models import User
from django.contrib.auth import login
from django.shortcuts import redirect
from django.contrib import messages
from django.contrib.auth import logout as auth_logout # Add this import at the top
def logout_view(request):
    auth_logout(request)
    return redirect('fitness:login') # Redirects to your login page
def signup(request):
    if request.method == "POST":
        u_name = request.POST.get("username")
        email = request.POST.get("email")
        pass_1 = request.POST.get("password")
        pass_2 = request.POST.get("confirm_password")

        # 1. Check if passwords match
        if pass_1 != pass_2:
            messages.error(request, "Passwords do not match.")
            return render(request, "registration/signup.html")

        # 2. Check if Email already exists
        if User.objects.filter(email=email).exists():
            messages.error(request, "A user with this email already exists.")
            return render(request, "registration/signup.html")
            
        # 3. Check if Username already exists
        if User.objects.filter(username=u_name).exists():
            messages.error(request, "Username is already taken.")
            return render(request, "registration/signup.html")

        # 4. Create the user
        user = User.objects.create_user(username=u_name, email=email, password=pass_1)
        user.save()
        
        # Log them in immediately and go to dashboard
        login(request, user)
        return redirect("fitness:index") 

    return render(request, "registration/signup.html")
@login_required
def index(request):
    """Render the main fitness tracker template.

    Calling get_token() forces Django to set the csrftoken cookie on the
    response so the front-end JS can read it from document.cookie and attach
    it as the X-CSRFToken header on every fetch() POST request.
    """
    get_token(request)  # ensures csrftoken cookie is present in the response

    context = {
        "api_data_url": reverse("fitness:fitness_data"),
        "api_log_url":  reverse("fitness:log_entry"),
    }
    return render(request, "index.html", context)

@login_required
def get_fitness_data(request):
    if request.method != "GET":
        return JsonResponse({"success": False, "error": "Method not allowed."}, status=405)
   
    logs = FatLossLog.objects.filter(user=request.user)

    data = [
        {
            "date": log.date.isoformat(),
            "goal_completion": log.goal_completion,
            "weight": log.weight,
            "waist_size": log.waist_size,
            "thigh_size": log.thigh_size,
            "bmi": log.bmi,  # computed property on the model
        }
        for log in logs
    ]

    return JsonResponse({"data": data})


@login_required
def log_entry(request):
    """Only POST is supported; return 405 explicitly for everything else."""
    if request.method != "POST":
        return JsonResponse(
            {"success": False, "error": "Method not allowed. Use POST."},
            status=405,
        )
    content_type = request.content_type or ""
    if "application/json" in content_type:
        try:
            body = json.loads(request.body)
        except json.JSONDecodeError:
            return JsonResponse(
                {"success": False, "errors": {"__all__": "Invalid JSON body."}},
                status=400,
            )
    else:
        body = request.POST

    errors = {}

    # --- goal_completion ---
    raw_goal = body.get("goal_completion", "").lower() if hasattr(body.get("goal_completion", ""), "lower") else body.get("goal_completion")
    if raw_goal in (True, 1, "true", "1", "on", "yes"):
        goal_completion = True
    elif raw_goal in (False, 0, "false", "0", "", "no", None):
        goal_completion = False
    else:
        errors["goal_completion"] = f"Invalid value '{raw_goal}'. Expected true or false."

    # --- weight ---
    try:
        weight = float(body.get("weight", ""))
        if weight <= 0:
            raise ValueError
    except (TypeError, ValueError):
        errors["weight"] = "Weight must be a positive number."

    # --- waist_size ---
    try:
        waist_size = float(body.get("waist_size", ""))
        if waist_size <= 0:
            raise ValueError
    except (TypeError, ValueError):
        errors["waist_size"] = "Waist size must be a positive number."

    # --- thigh_size ---
    try:
        thigh_size = float(body.get("thigh_size", ""))
        if thigh_size <= 0:
            raise ValueError
    except (TypeError, ValueError):
        errors["thigh_size"] = "Thigh size must be a positive number."

    if errors:
        return JsonResponse({"success": False, "errors": errors}, status=400)

    # All fields valid — persist to database
    log = FatLossLog.objects.create(
        user=request.user,
        goal_completion=goal_completion,
        weight=weight,
        waist_size=waist_size,
        thigh_size=thigh_size,
    )

    return JsonResponse(
        {
            "success": True,
            "id": log.id,
            "date": log.date.isoformat(),
            "bmi": log.bmi,
        },
        status=201,
    )
