from json.decoder import JSONDecodeError
import requests
import json
import os
import time


class OAuth2Connector:

    DEFAULT_REQUEST_TIMEOUT = 5  # seconds for general requests
    ONLINE_CHECK_TIMEOUT = 2    # seconds for online check

    api_base_url = None
    authorize_url = None
    token_url = None
    client_id = None
    client_secret = None
    callback_uri = None
    scopes = []

    tokens = None
    is_online = False # Assume offline by default until a check proves otherwise
    last_online_check_time = 0
    ONLINE_CHECK_INTERVAL = 60 # seconds, check online status at most once per minute

    def __init__(self, **kwargs):
        # initialize
        self.api_base_url = kwargs['api_base_url']
        self.authorize_url = kwargs['authorize_url']
        self.token_url = kwargs['token_url']
        self.client_id = kwargs['client_id']
        self.client_secret = kwargs['client_secret']
        self.callback_uri = kwargs['callback_uri']
        self.scopes = kwargs['scopes']
        self.check_online_status(force_check=True) # Initial online check

    def check_online_status(self, force_check=False):
        """
        Checks if the Home Connect API base URL is reachable.
        Updates self.is_online. To avoid spamming, subsequent calls within
        ONLINE_CHECK_INTERVAL will return the cached status unless force_check is True.
        Returns the current online status (boolean).
        """
        current_time = time.time()
        if not force_check and (current_time - self.last_online_check_time) < self.ONLINE_CHECK_INTERVAL:
            return self.is_online

        self.last_online_check_time = current_time
        if not self.api_base_url:
            self.is_online = False
            return False
        try:
            # Use a lightweight HEAD request if allowed, otherwise GET.
            # Ensure a timeout to prevent long hangs when offline.
            response = requests.head(self.api_base_url, timeout=self.ONLINE_CHECK_TIMEOUT, verify=False) # verify=False for consistency with existing code
            # Consider status codes that indicate online (e.g., 200-299, 404 might also mean server is up)
            self.is_online = response.status_code < 500 # Basic check, server is reachable
        except requests.exceptions.RequestException:
            self.is_online = False

        # Fallback for servers that might not support HEAD or have strict root path access
        if not self.is_online:
            try:
                # Attempt a GET request to a common, likely available, unauthenticated endpoint if one exists,
                # or just the base URL. Here, just trying base URL as a simple reachability.
                response = requests.get(self.api_base_url, timeout=self.ONLINE_CHECK_TIMEOUT, verify=False)
                self.is_online = response.status_code < 500
            except requests.exceptions.RequestException:
                self.is_online = False

        # print(f"Online status: {self.is_online}") # For debugging
        return self.is_online

    def set_tokens(self, tokens):
        """
        Save new set of tokens
        """
        self.tokens = tokens


    def _parse_access_token_response(self, response):
        """
        Process the response form token_url requests
        """
        status, result = self._handle_response(response)
        if "access_token" in result:
            self.set_tokens(result)
            return status, {"success": True}
        else:
            return status, result


    def refresh_access_token(self):
        """
        Refresh the current access_token using the refresh_token, if available
        """
        if not self.check_online_status():
            return 503, {'error': 'offline', 'message': 'Cannot refresh token while offline.'} # 503 Service Unavailable
        if not self.tokens or 'refresh_token' not in self.tokens:
            return 401, {'error': 'no refresh token set'}

        data = {'grant_type': 'refresh_token', 'refresh_token': self.tokens['refresh_token']}
        try:
            access_token_response = requests.post(
                self.token_url,
                data=data,
                verify=False,
                allow_redirects=False,
                auth=(self.client_id, self.client_secret),
                timeout=self.DEFAULT_REQUEST_TIMEOUT
            )
            self.is_online = True # Successful request implies online
        except requests.exceptions.RequestException as e:
            self.is_online = False
            return 503, {'error': 'offline', 'message': f'Network error during token refresh: {e}'}
        return self._parse_access_token_response(access_token_response)


    def request_access_token(self, code):
        """
        Request an access_token using an authorization_code
        """
        if not self.check_online_status():
            return 503, {'error': 'offline', 'message': 'Cannot request access token while offline.'}

        data = {'grant_type': 'authorization_code', 'code': code, 'valid_for': 86400, 'redirect_uri': self.callback_uri}
        try:
            access_token_response = requests.post(
                self.token_url,
                data=data,
                verify=False,
                allow_redirects=False,
                auth=(self.client_id, self.client_secret),
                timeout=self.DEFAULT_REQUEST_TIMEOUT
            )
            self.is_online = True
        except requests.exceptions.RequestException as e:
            self.is_online = False
            return 503, {'error': 'offline', 'message': f'Network error during access token request: {e}'}
        return self._parse_access_token_response(access_token_response)


    def _handle_response(self, request_response):
        """
        Try to parse the response and return tuple of (statusCode, body)
        """
        data = {}
        try:
            data = json.loads(request_response.text)
        except JSONDecodeError:
            data = {
                "response_text": request_response.text
            }
        status = request_response.status_code
        return status, data


    def get(self, endpoint):
        """
        Make an authenticated GET request to the API
        """
        # Note: Offline caching logic will be primarily in HomeconnectConnector subclass,
        # this base method will just check online status for non-cacheable GETs or if cache miss.
        if not self.check_online_status():
            # Specific caching logic will be in the subclass.
            # For a generic GET, if offline, it's an error unless handled by subclass.
            return 503, {'error': 'offline', 'message': f'Cannot make GET request to {endpoint} while offline.'}

        if not self.tokens or 'access_token' not in self.tokens:
            return 401, {'error': 'unauthorized', 'message': "Not authenticated. Call GET /auth first to authenticate."}

        try:
            request_response = requests.get(
                self.api_base_url + endpoint,
                headers={'Authorization': 'Bearer ' + self.tokens['access_token']},
                verify=False, # as per original code
                timeout=self.DEFAULT_REQUEST_TIMEOUT
            )
            self.is_online = True # Successful request implies online
        except requests.exceptions.RequestException as e:
            self.is_online = False
            return 503, {'error': 'offline', 'message': f'Network error during GET {endpoint}: {e}'}

        return self._handle_response(request_response)


    def put(self, endpoint, data):
        """
        Make an authenticated PUT request to the API.
        Offline queuing logic will be in HomeconnectConnector subclass.
        """
        if not self.check_online_status():
            # Specific queuing logic will be in the subclass.
            # For a generic PUT, if offline, it's an error unless handled by subclass.
            return 503, {'error': 'offline', 'message': f'Cannot make PUT request to {endpoint} while offline.'}

        if not self.tokens or 'access_token' not in self.tokens:
            return 401, {'error': 'unauthorized', 'message': "Not authenticated. Call GET /auth first to authenticate."}

        try:
            request_response = requests.put(
                self.api_base_url + endpoint,
                json=data,
                headers={
                    'Authorization': 'Bearer ' + self.tokens['access_token'],
                    "Content-Type": "application/vnd.bsh.sdk.v1+json"
                },
                verify=False, # as per original code
                timeout=self.DEFAULT_REQUEST_TIMEOUT
            )
            self.is_online = True
        except requests.exceptions.RequestException as e:
            self.is_online = False
            return 503, {'error': 'offline', 'message': f'Network error during PUT {endpoint}: {e}'}

        return self._handle_response(request_response)


    def get_authorization_url(self):
        """
        Get the URL to login at the provider
        """
        return self.authorize_url + '?response_type=code&client_id=' + self.client_id + '&redirect_uri=' + self.callback_uri + '&scope='+" ".join(self.scopes)



class PersistentOAuth2Connector(OAuth2Connector):

    path = None

    def __init__(self, **kwargs):
        # init and save path
        super().__init__(**kwargs)
        self.path = kwargs['path']
        self._load_config_from_file()

    def set_tokens(self, tokens):
        # overwrite set_tokens, also save to file
        super().set_tokens(tokens)
        self.save_config()

    def _save_config_to_file(self, config):
        """
        Save config to file
        """
        with open(self.path, "w") as f:
            json.dump(config, f)
    
    def _load_config_from_file(self):
        """
        Load config from file
        """
        try:
            if os.path.isfile(self.path):
                with open(self.path) as f:
                    fc = json.load(f)
                    self.load_config(fc)
        except Exception as e:
            print("Not able to load tokens from file", str(e))

    def load_config(self, config):
        if 'auth' not in config or 'access_token' not in config['auth']:
            # If no valid auth token in config, it's not necessarily a startup error.
            # User might need to authenticate for the first time.
            print("No valid access token found in config file. User may need to authenticate.")
            self.tokens = None # Ensure tokens are cleared
            return # Exit without error, allow app to prompt for login.

        self.set_tokens(config['auth']) # This just sets self.tokens

        # Try to refresh the token only if online
        if self.check_online_status():
            print("Attempting to refresh access token during load...")
            status_code, refresh_result = self.refresh_access_token()
            if status_code == 503 and refresh_result.get('error') == 'offline':
                print("Offline: Skipping token refresh during load. Will use existing token.")
            elif 'success' not in refresh_result:
                # Log error but don't necessarily prevent startup if tokens are usable.
                # The app might still function in a limited way or with cached data.
                print(f"Warning: Not able to refresh access_token during load: {refresh_result}. Current tokens might be stale.")
                # Depending on strictness, could raise RuntimeError here if fresh tokens are critical at load.
                # For offline capability, we prefer to continue with potentially stale tokens if that's all we have.
            else:
                print("Access token refreshed successfully during load.")
        else:
            print("Offline: Skipping token refresh during load. Will use existing token.")


    def save_config(self):
        # This method will be overridden in HomeconnectConnector to save more data
        return self._save_config_to_file({
            "auth": self.tokens
        })