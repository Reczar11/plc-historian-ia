import requests


class ApiClient:
    def __init__(self, base_url):
        self.base_url = base_url.rstrip('/')
        self.token = None
        self.role = None
        self.username = None

    def login(self, username, password):
        response = requests.post(
            self.base_url + '/auth/login',
            json={'username': username, 'password': password},
            timeout=5,
        )
        if response.status_code != 200:
            raise ValueError(response.json().get('detail', 'Login failed'))
        data = response.json()
        self.token = data['access_token']
        self.role = data['role']
        self.username = username
        return data

    def auth_headers(self):
        return {'Authorization': 'Bearer ' + str(self.token)}

    def get_assets_tree(self):
        response = requests.get(self.base_url + '/assets/tree', headers=self.auth_headers(), timeout=5)
        response.raise_for_status()
        return response.json()

    def get_tags(self):
        response = requests.get(self.base_url + '/tags', headers=self.auth_headers(), timeout=5)
        response.raise_for_status()
        return response.json()

    def get_alarms(self, status='active'):
        response = requests.get(
            self.base_url + '/alarms',
            params={'status': status},
            headers=self.auth_headers(),
            timeout=5,
        )
        response.raise_for_status()
        return response.json()
