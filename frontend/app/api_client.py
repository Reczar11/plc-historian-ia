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

    def create_tag(self, tag):
        response = requests.post(
            self.base_url + '/tags',
            json=tag,
            headers=self.auth_headers(),
            timeout=5,
        )
        if response.status_code not in (200, 201):
            raise ValueError(response.json().get('detail', 'Could not create tag'))
        return response.json()

    def update_tag(self, tag_id, tag):
        response = requests.put(
            self.base_url + f'/tags/{tag_id}',
            json=tag,
            headers=self.auth_headers(),
            timeout=5,
        )
        if response.status_code != 200:
            raise ValueError(response.json().get('detail', 'Could not update tag'))
        return response.json()

    def delete_tag(self, tag_id):
        response = requests.delete(
            self.base_url + f'/tags/{tag_id}',
            headers=self.auth_headers(),
            timeout=5,
        )
        if response.status_code != 200:
            raise ValueError(response.json().get('detail', 'Could not delete tag'))
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

    def acknowledge_alarm(self, alarm_id):
        response = requests.post(
            self.base_url + f'/alarms/{alarm_id}/acknowledge',
            headers=self.auth_headers(),
            timeout=5,
        )
        response.raise_for_status()
        return response.json()

    def get_readings(self, tag_name, start, end, resolution='raw'):
        response = requests.get(
            self.base_url + '/readings',
            params={'tag_name': tag_name, 'start': start, 'end': end, 'resolution': resolution},
            headers=self.auth_headers(),
            timeout=5,
        )
        response.raise_for_status()
        return response.json()

    def get_users(self):
        response = requests.get(self.base_url + '/users', headers=self.auth_headers(), timeout=5)
        if response.status_code != 200:
            raise ValueError(response.json().get('detail', 'Could not load users'))
        return response.json()

    def create_user(self, username, password, role):
        response = requests.post(
            self.base_url + '/users',
            json={'username': username, 'password': password, 'role': role},
            headers=self.auth_headers(),
            timeout=5,
        )
        if response.status_code not in (200, 201):
            raise ValueError(response.json().get('detail', 'Could not create user'))
        return response.json()

    def update_user(self, user_id, password=None, role=None):
        payload = {}
        if password is not None:
            payload['password'] = password
        if role is not None:
            payload['role'] = role
        response = requests.put(
            self.base_url + f'/users/{user_id}',
            json=payload,
            headers=self.auth_headers(),
            timeout=5,
        )
        if response.status_code != 200:
            raise ValueError(response.json().get('detail', 'Could not update user'))
        return response.json()

    def delete_user(self, user_id):
        response = requests.delete(
            self.base_url + f'/users/{user_id}',
            headers=self.auth_headers(),
            timeout=5,
        )
        if response.status_code != 200:
            raise ValueError(response.json().get('detail', 'Could not delete user'))
        return response.json()

    def export_excel_report(self, tags, start, end, resolution='1min'):
        response = requests.post(
            self.base_url + '/reports/excel',
            json={'tags': tags, 'start': start, 'end': end, 'resolution': resolution},
            headers=self.auth_headers(),
            timeout=30,
        )
        if response.status_code != 200:
            try:
                detail = response.json().get('detail', 'Could not generate report')
            except Exception:
                detail = 'Could not generate report'
            raise ValueError(detail)
        return response.content

    def get_plc_config(self):
        response = requests.get(self.base_url + '/plc/config', headers=self.auth_headers(), timeout=5)
        if response.status_code != 200:
            raise ValueError(response.json().get('detail', 'Could not load PLC config'))
        return response.json()

    def update_plc_config(self, plc_ip, data_source, port=None, unit_id=None):
        response = requests.put(
            self.base_url + '/plc/config',
            json={'plc_ip': plc_ip, 'data_source': data_source, 'port': port, 'unit_id': unit_id},
            headers=self.auth_headers(),
            timeout=5,
        )
        if response.status_code != 200:
            raise ValueError(response.json().get('detail', 'Could not save PLC config'))
        return response.json()
