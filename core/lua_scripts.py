RATE_LIMIT_LUA = """
-- KEYS[1] = redis_key
-- ARGV[1] = current timestamp
-- ARGV[2] = window
-- ARGV[3] = limit

local key = KEYS[1]
local strike_key = KEYS[2]
local ban_key = KEYS[3]

local now = tonumber(ARGV[1])
local window = tonumber(ARGV[2])
local limit = tonumber(ARGV[3])

local max_strikes = tonumber(ARGV[4])
local ban_time = tonumber(ARGV[5])


-- Check if banned
if redis.call('EXISTS', ban_key) == 1 then
    return {2, 0}  -- banned
end


local window_start = now - window

-- Removes all requests older than the window
redis.call('ZREMRANGEBYSCORE', key, 0, window_start)

local count = redis.call('ZCARD', key)

if count >= limit then
    local strikes = redis.call('INCR', strike_key)
    redis.call('EXPIRE', strike_key, window) -- Set expiry for strikes
    
    -- check for ban
    if strikes >= max_strikes then
        redis.call('SET', ban_key, 1) -- Ban the user
        redis.call('EXPIRE', ban_key, ban_time) 
        redis.call('DEL', strike_key) -- Reset strikes after banning
        
        return {3, strikes} -- banned
    end
    
     return {0, strikes}  -- rate limited
end


redis.call('ZADD', key, now, tostring(now) .. '-' .. tostring(now) .. '-' .. tostring(math.random())) -- If 2 requests come in same second → collision => used the :: .. - .. math.random() to make it unique
redis.call('EXPIRE', key, window)

return {1, count + 1} -- allowed
"""