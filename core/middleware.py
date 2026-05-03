from django.http import JsonResponse
from core.redis_client import redis_client
from core.models import APIKey
from .views import hash_key
import time
from django.utils import timezone


EXCLUDED_PATHS = ["/signup/", "/login/", "/logout/", "/regenerate-key/"]

class RateLimitMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response
        self.DEFAULT_LIMIT = 10
        self.DEFAULT_WINDOW = 30
        self.BAN_TIME = 24 * 60 * 60 # 24 hours
        self.MAX_STRIKES = 3
        
    def __call__(self, request):
        if request.path in EXCLUDED_PATHS:
            return self.get_response(request)
        
        incoming_api_key_value = request.headers.get("X-API-KEY")
        
        if incoming_api_key_value:
            hashed_key = hash_key(incoming_api_key_value)
            
            try:
                api_key_obj = APIKey.objects.get(api_key=hashed_key)
                
                if  api_key_obj.is_active == False and api_key_obj.expires_at < timezone.now():
                    return JsonResponse({"error": "API Key is inactive"}, status=403)
                
            except APIKey.DoesNotExist:
                return JsonResponse({"error": "Invalid API Key"}, status=403)
            
            redis_key = f"rate_limit:apikey:{api_key_obj.api_key}"
            limit = api_key_obj.rate_limit
            window = api_key_obj.window
            
            
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
        now = time.time()
        window_start = now - window
        # Remove all requests older than window
        redis_client.zremrangebyscore(redis_key, 0, window_start)
        # Count current requests
        count = redis_client.zcard(redis_key)
        
        
        #Limit exceedes
        if count >= limit:
            strikes = redis_client.incr(strike_key)
            redis_client.expire(strike_key, window) # Remove the strike_key after `window` time
            
            print(f"Identifier: {identifier}, Strikes: {strikes}")
            
            if strikes >= self.MAX_STRIKES:
                redis_client.set(ban_key, 1, ex=self.BAN_TIME)
                redis_client.delete(strike_key) # Reset strikes after banning
                
                return JsonResponse(
                    {
                        "error": "You have been temporarily banned due to repeated rate limit violations."
                    }, status=403
                )
            
            return JsonResponse(
                {"error": "Too many requests."}, 
                status=429,
                headers={
                  "X-RateLimit-Limit": str(limit),
                  "X-RateLimit-Remaining": "0",
                }
            )
            
        # Add current request
        redis_client.zadd(redis_key, {str(now): now})
        
        # Expire key - Delete this key after `window` seconds
        redis_client.expire(redis_key, window)
        
        remaining = max(0, limit - (count + 1))
        
        if not incoming_api_key_value:
            print(f"IP: {client_ip}, Count: {count}")
        else: 
            print(f"User: {api_key_obj.user.username}, Count: {count}")
            
        
            
        response = self.get_response(request)
        response["X-RateLimit-Limit"] = str(limit)
        response["X-RateLimit-Remaining"] = str(remaining)
        
        return response
    
    def get_client_ip(self, request):
         return request.META.get("REMOTE_ADDR", 'unknown')
        