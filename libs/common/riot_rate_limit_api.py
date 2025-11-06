import requests, threading, os, time
from collections import defaultdict
class RiotRateLimitAPI:
    def __init__(self):
         # Get the Riot Token, then set the token as a header param in request.Session
        if os.getenv('ENV', 'local') == 'local':
            from dotenv import load_dotenv
            assert load_dotenv() == True
        self.session = requests.Session()
        self.__api_key = os.environ['RIOT_API_KEY']
        assert self.__api_key is not None
        self.session.headers.update({
            'X-Riot-Token': self.__api_key
        })
        self.rate_limits = []
        self.rate_history = defaultdict(list)
        # use threading lock to update rate limits
        self.lock = threading.Lock()
    
    def parse_rate_header(self, rate_header: str):
        '''
        Parses the 'X-Rate-Limit' header from Riot Endpoints to get the rate limits

        Returns a list of tuples (count, sec). Ex: rate_header = 20:1,100:120 means that user is
        allowed to call 20 times per second and 100 times per 2 minutes
        '''
        parts = []
        for rates in rate_header.split(','):
            count, sec = rates.split(':')
            parts.append((int(count), int(sec)))

        return parts

    def wait_for_request_slot(self, rate_limits: list[tuple[int, int]], rate_history: dict[list]):
        '''
        Blocks all requests until rate windows are within limits
        '''

        with self.lock:
            now = time.time()
            for limit, window in rate_limits:
                # Remove timestamps older than window
                rate_history[window] = [t for t in rate_history[window] if now - t < window]
                # If at limit, wait until the earliest timestamp expires
                if len(rate_history[window]) >= limit:
                    sleep_time = window - (now - rate_history[window][0]) + 0.01
                    time.sleep(sleep_time)

            for _, window in rate_limits:
                rate_history[window].append(time.time())

    def call_endpoint_with_rate_limit(self, url: str, rate_limits: list[tuple[int, int]] = None, rate_history: dict[list] = None, max_retries: int = 6):
        backoff = 0.5
        if not rate_history:
            rate_history = self.rate_history
        if not rate_limits:
            rate_limits = self.rate_limits
            
        for _ in range(max_retries):
            try:
                self.wait_for_request_slot(rate_limits, rate_history)
                response = self.session.get(url)
                if response.status_code == 200:
                    if not rate_limits:
                        rate_limits.extend(self.parse_rate_header(response.headers.get('X-App-Rate-Limit', '')))
                    return response.json()
                elif response.status_code == 429:
                    retry_after = float(response.headers.get('Retry-After', 1))
                    print(f'Rate limited, sleeping for {retry_after}s...')
                    time.sleep(retry_after)
                else:
                    print(f'Server error {response.status_code}, retrying in {backoff}s...')
                    time.sleep(backoff)
                    backoff *= 2
                    response.raise_for_status()
            except requests.exceptions.HTTPError as e:
                print('Request Error:', e)
                
        return None