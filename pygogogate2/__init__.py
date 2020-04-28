import requests
import logging
from xml.etree import ElementTree
from Cryptodome.Cipher import AES
import base64
import uuid
from urllib.parse import urlencode, quote_plus


class Gogogate2API:
    """Class for interacting with the Gogogate2 App API."""

    APP_ID = '0e3b7%i1X9@54cAf'

    STATE_OPEN = 'open'
    STATE_CLOSED = 'closed'
    STATE_ACTIVATING = 'activating'

    USERAGENT = "okhttp/3.9.1"

    REQUEST_TIMEOUT = 3.0

    DOOR_STATE = {
        'opened': STATE_OPEN,  # 'open',
        'closed': STATE_CLOSED,  # 'close'
    }

    logger = logging.getLogger(__name__)

    def __init__(self, username, password, ip_address):
        """Initialize the API object."""
        self.username = username
        self.password = password
        if ip_address is not None:
            self.host_uri = 'http://' + ip_address
        self.api_code = None
        self._logged_in = False
        self._device_states = {}
        self.cipher = AESCipher(self.APP_ID)
        self.apicode = None

    def make_request(self, command):
        try:
            command = self.cipher.encrypt(command)
            payload = {'data': command}
            query = urlencode(payload, quote_via=quote_plus)
            devices = requests.get(
                '{host_uri}/api.php?{query}'.format(
                    host_uri=self.host_uri,
                    query=query),
                headers={
                    'User-Agent': self.USERAGENT
                },
                timeout=self.REQUEST_TIMEOUT
            )

            devices.raise_for_status()
        except requests.exceptions.HTTPError as ex:
            self.logger.error('Gogogte2 - API Error[make_request] %s', ex)
            return False

        try:
            content = self.cipher.decrypt(devices.content)
            tree = ElementTree.fromstring(content)
            return tree
        except:
            KeyError
        self.logger.error('Gogogate2 - Login secirty token may have expired, will attempt relogin on next attempt')


    def get_devices(self):
        """List all garage door devices."""
        devices = self.make_request('["{username}","{password}","info","",""]'.format(
            username=self.username,
            password=self.password))

        if devices != False:
            garage_doors = []

            try:
                apicode_element = devices.find('apicode')
                if apicode_element is None:
                    self.logger.error('Gogogate2 - Invalid username or password provided.')
                    return False

                self.apicode = apicode_element.text
                self._device_states = {}
                for doorNum in range(1, 4):
                    door = devices.find('door' + str(doorNum))
                    doorName = door.find('name').text
                    if doorName:
                        dev = {'door': doorNum, 'name': doorName}
                        for id in ['mode', 'sensor', 'status', 'sensorid', 'temperature', 'voltage',
                                   'camera', 'events', 'permission']:
                            item = door.find(id)
                            if item is not None:
                                dev[id] = item.text
                        garage_state = door.find('status').text
                        dev['status'] = self.DOOR_STATE[garage_state]
                        self._device_states[doorNum] = self.DOOR_STATE[garage_state]
                        garage_doors.append(dev)

                return garage_doors
            except TypeError as ex:
                print(ex)
                return False
        else:
            return False


    def get_status(self, device_id):
        """List only MyQ garage door devices."""
        devices = self.get_devices()

        if devices != False:
            for device in devices:
                if device['door'] == device_id:
                    return device['status']

        return False

    def get_temperature(self, device_id):
        """List only MyQ garage door devices."""
        devices = self.get_devices()

        if devices != False:
            for device in devices:
                if device['door'] == device_id:
                    temp = device.get('temperature')
                    if temp is None:
                        return False

                    # gogogate returns '-1000000' when the door does not have a value
                    if temp == "-1000000":
                        return 0.0
                    else:
                        celcius = float(temp)
                        return celcius
        return False

    def activate(self, device_id, expected_current_state):
        if not self.apicode:
            self.get_devices()

        if device_id in self._device_states:
            current_state = self._device_states[device_id]
            if expected_current_state != current_state:
                self.logger.warning('Gogogate2 - Will not activate. Device not in expected current state %s. Actual state %s', expected_current_state, current_state)
                return False

        
        self._device_states[device_id] = self.STATE_ACTIVATING

        response = self.make_request('["{username}","{password}","activate","{device_id}","{apicode}"]'.format(
            username=self.username,
            password=self.password,
            apicode=self.apicode,
            device_id=device_id))
        return response


    def close_device(self, device_id):
        """Close Gogogate Device."""
        return self.activate(device_id, self.STATE_OPEN)


    def open_device(self, device_id):
        """Open Gogogate Device."""
        return self.activate(device_id, self.STATE_CLOSED)


BS = 16
pad = lambda s: s + (BS - len(s) % BS) * chr(BS - len(s) % BS)
unpad = lambda s: s[0:-s[-1]]


class AESCipher:
    def __init__(self, key):
        self.key = key.encode('utf-8')

    def encrypt(self, raw):
        raw = pad(raw).encode('utf-8')
        iv = uuid.uuid4().hex[: AES.block_size].encode('utf-8')
        cipher = AES.new(self.key, AES.MODE_CBC, iv)
        return str(iv + base64.b64encode(cipher.encrypt(raw)), 'utf-8')

    def decrypt(self, enc):
        iv = enc[:16]
        enc = base64.b64decode(enc[16:])
        cipher = AES.new(self.key, AES.MODE_CBC, iv)
        return unpad(cipher.decrypt(enc))
