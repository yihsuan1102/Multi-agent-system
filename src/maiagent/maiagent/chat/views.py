from django.contrib.auth.decorators import login_required
from django.shortcuts import render
from django.views.decorators.http import require_http_methods


@require_http_methods(["GET"])
def login_view(request):
    """Chat login page"""
    return render(request, "chat/login.html")


@login_required
@require_http_methods(["GET"])
def chat_room_view(request):
    """Chat room page"""
    return render(request, "chat/room.html")