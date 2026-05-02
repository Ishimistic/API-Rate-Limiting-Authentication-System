from django.http import JsonResponse
from django.contrib.auth.models import User
from django.contrib.auth import authenticate, login, logout
from django.views.decorators.csrf import csrf_exempt
import json
from core.models import APIKey


def test_api(request):
    return JsonResponse({"message": "API working"})


@csrf_exempt
def signup(request):
    if request.method == "POST":
        data = json.loads(request.body)
        username = data.get("username")
        password = data.get("password")
        
        if User.objects.filter(username=username).exists():
            return JsonResponse({"error": "Username already exists"}, status=400)
        
        user = User.objects.create_user(username=username, password=password)
        
        api_key = APIKey.objects.create(user=user)
        
        return JsonResponse({
            "message": "User created successfully",
            "api_key": api_key.api_key
        },status=201)
        
        
@csrf_exempt       
def login_view(request):
    if request.method == "POST":
        data = json.loads(request.body)
        username = data.get("username")
        password = data.get("password")
        
        user = authenticate(username=username, password=password)
        
        if user is  None:
            return JsonResponse({"error": "Invalid credentials"}, status=401)
        
        api_key = APIKey.objects.filter(user=user).first()
        
        return JsonResponse({"message": "Login successful"}, headers={"X-API-KEY": api_key.api_key}, status=200)
    
    
def logout_view(request):
    api_key_value = request.headers.get("X-API-KEY")

    if api_key_value:
        APIKey.objects.filter(api_key=api_key_value).delete()
        
    logout(request)
    return JsonResponse({"message": "Logout successful"}, status=200)