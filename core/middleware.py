from django.http import JsonResponse
from core.redis_client import redis_client
from core.models import APIKey
from .views import hash_key
import time
from django.utils import timezone
from core.lua_scripts import RATE_LIMIT_LUA
from core.plans import PLAN_LIMITS


EXCLUDED_PATHS = ["/signup/", "/login/", "/logout/", "/regenerate-key/"]

class RateLimitMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response
        self.DEFAULT_LIMIT = 10
        self.DEFAULT_WINDOW = 30
        self.BAN_TIME = 24 * 60 * 60 # 24 hours
        self.MAX_STRIKES = 3
        
    def __call__(self, request):
        if any(request.path.startswith(path) for path in EXCLUDED_PATHS):
            return self.get_response(request)
        
        incoming_api_key_value = request.headers.get("X-API-KEY")
        
        if incoming_api_key_value:
            hashed_key = hash_key(incoming_api_key_value)
            
            try:
                api_key_obj = APIKey.objects.get(api_key=hashed_key)
                
                if not api_key_obj.is_active:
                    return JsonResponse({"error": "API key inactive"}, status=403)

                if api_key_obj.expires_at and api_key_obj.expires_at < timezone.now():
                    return JsonResponse({"error": "API key expired"}, status=403)
                
            except APIKey.DoesNotExist:
                return JsonResponse({"error": "Invalid API Key"}, status=403)
            
            redis_key = f"rate_limit:apikey:{api_key_obj.api_key}"
            
            plan = api_key_obj.plan
            plan_config = PLAN_LIMITS.get(plan, PLAN_LIMITS['free'])
            
            limit = plan_config['limit']
            window = plan_config['window']

        else:
            client_ip = self.get_client_ip(request) # Identify client
            if client_ip == 'unknown':
                client_ip = 'global'
        
            redis_key = f"rate_limit:{client_ip}"
            limit = self.DEFAULT_LIMIT
            window = self.DEFAULT_WINDOW
            
        identifier = redis_key
        ban_key = f"ban:{identifier}"
        strike_key = f"strike:{identifier}"
        
        # Checking ban 
        if redis_client.exists(ban_key):
            return JsonResponse(
                {
                    "error": "You are temporarily banned due to repeated rate limit violations."
                }, status=403
            )
         
         
        # Sliding window part   
        now = int(time.time())
       
        result = redis_client.eval(
            RATE_LIMIT_LUA,
            3, # Number of keys
            redis_key, # KEYS[1]
            strike_key, # KEY[2]
            ban_key, # KEY[3]
            now,
            window,
            limit,
            self.MAX_STRIKES,
            self.BAN_TIME
        )
        
        status = result[0]
        value = result[1]
        
        if status == 0:
            return JsonResponse(
                {
                    "error": "Too many requests."
                }, 
                status=429
            )
        
        if status == 2:
            return JsonResponse(
                {
                    "error": "You are temporarily banned."
                }, status=403
            )
            
        if status == 3:
            return JsonResponse(
                {
                    "error": "You have been banned."
                }, status=403
            )
            
        
        remaining = max(0, limit - value)
        response = self.get_response(request)

        response["X-RateLimit-Limit"] = str(limit)
        response["X-RateLimit-Remaining"] = str(remaining)

        return response
    
    
    def get_client_ip(self, request):
         return request.META.get("REMOTE_ADDR", 'unknown')
        