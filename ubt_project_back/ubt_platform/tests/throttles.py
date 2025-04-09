from rest_framework.exceptions import Throttled
from rest_framework.throttling import UserRateThrottle

class GenerateTestThrottle(UserRateThrottle):
    scope = 'generate_test'
    rate = '2/day'

    def allow_request(self, request, view):
        if not self.is_request_allowed(request):
            wait_time = self.wait()
            raise Throttled(
                detail="Rate limit exceeded. Please wait before retrying.",
                wait=wait_time
            )
        self.increment_request_count(request)
        return True

    def is_request_allowed(self, request):
        return super().allow_request(request, None)

    def increment_request_count(self, request):
        self.cache_key = self.get_cache_key(request, None)
        if self.cache_key:
            self.history = self.cache.get(self.cache_key, [])
            self.history.insert(0, self.timer())
            self.cache.set(self.cache_key, self.history, self.duration)

class SubmitAnswersThrottle(UserRateThrottle):
    scope = 'submit_answers'
    rate = '2/day'
