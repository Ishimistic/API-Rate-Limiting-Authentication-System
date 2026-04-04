from django.http import JsonResponse
from core.redis_client import redis_client

class RateLimitMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response
        self.LIMIT = 5
        self.WINDOW = 30
        
    def __call__(self, request):
        client_ip = self.get_client_ip(request) # Identify client
        redis_key = f"rate_limit:{client_ip}"
        
        if client_ip == 'unknown':
            client_ip = 'global'
        
        count = redis_client.get(redis_key) # get current count
        
        if count is None:
            redis_client.set(redis_key, 1, ex=self.WINDOW)
            count = 1
        else:
            count = redis_client.incr(redis_key)
            
        
        print(f"IP: {client_ip}, Count: {count}")
            
        
        if int(count) > self.LIMIT:
            return JsonResponse(
                {"error": "Too many requests."}
                , status=429
            )
            
        response = self.get_response(request)
        return response
    
    def get_client_ip(self, request):
         return request.META.get("REMOTE_ADDR", 'unknown')
        