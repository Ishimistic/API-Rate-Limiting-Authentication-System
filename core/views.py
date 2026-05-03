from django.http import JsonResponse
from django.contrib.auth.models import User
from django.contrib.auth import authenticate, login, logout
from django.views.decorators.csrf import csrf_exempt
import json
from core.models import APIKey
import secrets
import hashlib
from datetime import timedelta
from django.utils import timezone


def test_api(request):
    return JsonResponse({"message": "API working"})


def hash_key(key):
    return hashlib.sha256(key.encode()).hexdigest()


@csrf_exempt
def signup(request):
    if request.method == "POST":
        data = json.loads(request.body)
        username = data.get("username")
        password = data.get("password")
        
        if User.objects.filter(username=username).exists():
            return JsonResponse({"error": "Username already exists"}, status=400)
        
        user = User.objects.create_user(username=username, password=password)
        
        raw_key = secrets.token_hex(32)
        hashed = hash_key(raw_key)
        
        api_key = APIKey.objects.create(user=user, api_key=hashed, expires_at=timezone.now() + timedelta(hours=24))
        
        return JsonResponse(
            {
               "message": "User created successfully",
               "api_key": raw_key
            },status=201
        )
        
        
@csrf_exempt       
def login_view(request):
    if request.method == "POST":
        data = json.loads(request.body)
        username = data.get("username")
        password = data.get("password")
        
        user = authenticate(username=username, password=password)
        
        if user is  None:
            return JsonResponse({"error": "Invalid credentials"}, status=401)
        
        raw_key = secrets.token_hex(32)
        hashed = hash_key(raw_key)

        api_obj, _ = APIKey.objects.get_or_create(user=user)
        api_obj.api_key = hashed
        api_obj.is_active = True
        api_obj.expires_at = timezone.now() + timedelta(hours=24)
        api_obj.save()


        return JsonResponse({
            "message": "Login successful",
            "api_key": raw_key  
        })
    
    
    
def logout_view(request):
    api_key_value = request.headers.get("X-API-KEY")
    
    if not api_key_value:
        return JsonResponse({"error": "API Key required"}, status=400)
    
    hashed = hash_key(api_key_value)
    
    api_obj = APIKey.objects.filter(api_key=hashed).first()
    
    if api_obj:
        api_obj.is_active = False
        api_obj.save()
    
    else:
        print(f"Logout attempt with invalid API Key: {api_key_value}")
        return JsonResponse({"error": "Invalid API Key"}, status=403)
    
    return JsonResponse({"message": "Logout successful"}, status=200)



@csrf_exempt
def regenerate_api_key(request):
    api_key_value = request.headers.get("X-API-KEY")

    if not api_key_value:
        return JsonResponse({"error": "API key required"}, status=400)

    hashed = hash_key(api_key_value)

    api_obj = APIKey.objects.filter(api_key=hashed, is_active=True).first()

    if not api_obj:
        return JsonResponse({"error": "Invalid API key"}, status=403)

    new_raw = secrets.token_hex(32)
    new_hashed = hash_key(new_raw)

    api_obj.api_key = new_hashed
    api_obj.expires_at = timezone.now() + timedelta(hours=24)
    api_obj.save()

    return JsonResponse({
        "message": "API key regenerated",
        "api_key": new_raw
    })