import json

from django.http import JsonResponse
from django.middleware.csrf import get_token
from django.shortcuts import render
from django.urls import reverse
from django.views.decorators.csrf import csrf_exempt

from .models import FatLossLog


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


def get_fitness_data(request):
    if request.method != "GET":
        return JsonResponse({"success": False, "error": "Method not allowed."}, status=405)
    """
    Return all FatLossLog entries serialised as JSON for front-end graphs
    and UI components.

    Response shape:
    {
        "data": [
            {
                "date": "2024-06-01",
                "goal_completion": true,
                "weight": 80.5,
                "waist_size": 34.0,
                "thigh_size": 22.5,
                "bmi": 29.6
            },
            ...
        ]
    }
    """
    logs = FatLossLog.objects.all()  # already ordered by -date via Meta

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


@csrf_exempt
def log_entry(request):
    """Only POST is supported; return 405 explicitly for everything else."""
    if request.method != "POST":
        return JsonResponse(
            {"success": False, "error": "Method not allowed. Use POST."},
            status=405,
        )
    """
    Accept a POST request containing a new fitness log entry, validate the
    fields, persist the record, and return a JSON response.

    Expected POST body (application/json or form-encoded):
        goal_completion  – "true" / "false" / 1 / 0
        weight           – float
        waist_size       – float
        thigh_size       – float

    Successful response (HTTP 201):
        {"success": true, "id": <int>, "bmi": <float>, "date": "<iso-date>"}

    Error response (HTTP 400):
        {"success": false, "errors": {"field": "message", ...}}
    """
    # Support both JSON body and standard form-encoded POST
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
