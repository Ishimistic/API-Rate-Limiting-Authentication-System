from django.http import JsonResponse
from core.redis_client import redis_client
from core.models import APIKey

class RateLimitMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response
        self.DEFAULT_LIMIT = 10
        self.DEFAULT_WINDOW = 30
        
    def __call__(self, request):
        api_key_value = request.headers.get("X-API-KEY")
        
        if api_key_value:
            try:
                api_key_obj = APIKey.objects.get(api_key=api_key_value)
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
        
        count = redis_client.get(redis_key) # get current count
        
        if count is None:
            redis_client.set(redis_key, 1, ex=window)
            count = 1
        else:
            count = redis_client.incr(redis_key)
            
        remainig = max(0, limit - int(count))
            
        if not api_key_value:
            print(f"IP: {client_ip}, Count: {count}")
        else: 
            print(f"User: {api_key_obj.user.username}, Count: {count}")
            
        
        if int(count) > limit:
            return JsonResponse(
                {"error": "Too many requests."}, 
                status=429,
                headers={
                  "X-RateLimit-Limit": str(limit),
                  "X-RateLimit-Remaining": "0",
                }
            )
            
        response = self.get_response(request)
        response["X-RateLimit-Limit"] = str(limit)
        response["X-RateLimit-Remaining"] = str(remainig)
        
        return response
    
    def get_client_ip(self, request):
         return request.META.get("REMOTE_ADDR", 'unknown')
        