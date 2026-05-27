import time

fallback_store = {}

def fallback_rate_limit(identifier, limit, window):
    now = int(time.time())
    
    if identifier not in fallback_store:
        fallback_store[identifier] = []
        
    # Remove old timestamps
    fallback_store[identifier] = [
        t for t in fallback_store[identifier] if t > now - window
    ]
    
    # Check limit
    if len(fallback_store[identifier]) >= limit:
        return False, len(fallback_store[identifier])
    
    # Add current request
    fallback_store[identifier].append(now)
    
    return True, len(fallback_store[identifier])
    
    