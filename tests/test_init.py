"""Tests for gogogate2 api."""
import json
import unittest
from urllib.parse import parse_qs, urlparse

import requests
import requests_mock

from pygogogate2 import AESCipher, Gogogate2API


class MockGogoGateServer:
    def __init__(self):
        self.username: str = "username1"
        self.password: str = "password1"
        self.api_code: str = "api_code1"
        self.http_status: int = 200
        self._requests_mocker = requests_mock.Mocker()
        self._cipher = AESCipher(Gogogate2API.APP_ID)
        self._devices = {
            1: {
                "permission": "yes",
                "name": "Gate",
                "mode": "garage",
                "status": "closed",
                "sensor": "yes",
                "sensorid": "WIRE",
                "camera": "no",
                "events": 1234,
            },
            2: {
                "permission": "yes",
                "name": "Garage",
                "mode": "garage",
                "status": "opened",
                "sensor": "yes",
                "sensorid": "WIRE",
                "camera": "no",
                "events": 4321,
                "temperature": 13,
            },
        }

    def setUp(self) -> None:
        self._requests_mocker.start()
        self._requests_mocker.get("http://localhost/api.php", text=self._handle_request)

    def tearDown(self) -> None:
        self._requests_mocker.stop()

    def set_device_status(self, device_id: int, status: str) -> None:
        self._devices[device_id]["status"] = status

    def set_device_temperature(self, device_id: int, temperature: str) -> None:
        if temperature is None:
            del self._devices[device_id]["temperature"]
        else:
            self._devices[device_id]["temperature"] = temperature

    def _handle_request(self, request: requests.Request, context) -> str:
        context.status_code = self.http_status

        # Simulate an HTTP error.
        if context.status_code != 200:
            return ""

        # Parse the request.
        query = parse_qs(urlparse(request.url).query)
        data = query["data"][0]
        decrypted = self._cipher.decrypt(data.encode("utf-8"))
        payload = json.loads(decrypted)

        username = payload[0]
        password = payload[1]
        command = payload[2]

        # Validate credentials.
        if username != self.username or password != self.password:
            return self._new_response(
                """
                <error>
                    <errorcode>01</errorcode>
                    <errormsg>Error: wrong login or password</errormsg>
                </error>
            """
            )

        # Handle activation command.
        if command == "activate":
            device_id = int(payload[3])
            api_code = payload[4]

            if api_code != self.api_code:
                context.status_code = 401
                return self._new_response("")

            current_status = self._devices[device_id]["status"]
            self._devices[device_id]["status"] = (
                "closed" if current_status == "opened" else "opened"
            )

            return self._new_response(
                """
                <result>ok</result>
            """
            )

        # handle info command.
        if command == "info":
            self.api_code = "fjsll33"
            return self._new_response(
                f"""
                <user>{self.username}</user>
                <gogogatename>home</gogogatename>
                <model>GGG2</model>
                <apiversion>1.5</apiversion>
                <remoteaccessenabled>0</remoteaccessenabled>
                <remoteaccess>abcdefg12345.my-gogogate.com</remoteaccess>
                <firmwareversion>260\n</firmwareversion>
                <apicode>{self.api_code}</apicode>
                <door1>
                    {self._device_to_xml_str(1)}
                </door1>
                <door2>
                    {self._device_to_xml_str(2)}
                </door2>
                <door3>
                    <permission>yes</permission>
                    <name></name>
                    <mode>garage</mode>
                    <status>undefined</status>
                    <sensor>no</sensor>
                    <camera>no</camera>
                    <events>0</events>
                </door3>
                <outputs>
                    <output1>off</output1>
                    <output2>off</output2>
                    <output3>off</output3>
                </outputs>
                <network>
                    <ip>127.0.1.1</ip>            
                </network>
                <wifi>
                    <SSID></SSID>
                    <linkquality>61%</linkquality>
                    <signal>-67 dBm</signal>            
                </wifi>
            """
            )

        return self._new_response("")

    def _device_to_xml_str(self, device_id: int) -> str:
        device_dict = self._devices[device_id]
        return "\n".join(
            [f"<{key}>{value}</{key}>" for key, value in device_dict.items()]
        )

    def _new_response(self, xml_str: str) -> str:
        return self._cipher.encrypt(
            f"""<?xml version="1.0"?>
            <response>
                 {xml_str}
            </response>
        """
        )


class TestApi(unittest.TestCase):
    def setUp(self) -> None:
        self.server = MockGogoGateServer()
        self.server.setUp()
        self.api = Gogogate2API(self.server.username, self.server.password, "localhost")

    def tearDown(self) -> None:
        self.server.tearDown()

    def test_http_error(self) -> None:
        self.server.http_status = 503
        assert self.api.get_devices() is False

    def test_auth_failed(self) -> None:
        self.server.username = "a"
        self.api.username = "b"
        self.server.password = "a"
        self.api.password = "b"
        assert self.api.get_devices() is False

        self.server.username = "a"
        self.api.username = "a"
        assert self.api.get_devices() is False

    def test_open_close(self) -> None:
        assert self.api.open_device(1)
        assert self.api.get_status(1) == "open"
        assert self.api.close_device(1)
        assert self.api.get_status(1) == "closed"

        assert self.api.get_status(2) == "open"
        assert self.api.open_device(2) is False

    def test_get_temperature(self) -> None:
        assert self.api.get_temperature(1) is False
        assert self.api.get_temperature(2) == 13

        self.server.set_device_temperature(1, 10)
        assert self.api.get_temperature(1) == 10

        self.server.set_device_temperature(2, -1000000)
        assert self.api.get_temperature(2) == 0.0

        self.api.username = "invalid"
        assert self.api.get_temperature(2) is False
