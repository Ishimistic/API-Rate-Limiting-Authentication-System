from django.http import JsonResponse
from core.redis_client import redis_client

class RateLimitMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response
        self.LIMIT = 10
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
            
        
        remainig = max(0, self.LIMIT - int(count))
            
        
        print(f"IP: {client_ip}, Count: {count}")
            
        
        if int(count) > self.LIMIT:
            return JsonResponse(
                {"error": "Too many requests."}, 
                status=429,
                headers={
                  "X-RateLimit-Limit": str(self.LIMIT),
                  "X-RateLimit-Remaining": "0",
                }
            )
            
        response = self.get_response(request)
        response["X-RateLimit-Limit"] = str(self.LIMIT)
        response["X-RateLimit-Remaining"] = str(remainig)
        
        return response
    
    def get_client_ip(self, request):
         return request.META.get("REMOTE_ADDR", 'unknown')
        