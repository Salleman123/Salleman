# core/vmix_client.py
"""
vMix HTTP API Client
Clean implementation using only Python standard library
"""

import urllib.parse
import urllib.request
import xml.etree.ElementTree as ET
import socket
from typing import Optional


class VMixClient:
    """
    Simple client for vMix HTTP API.
    
    Base URL: http://host:port/api/
    Examples:
      - GET /api/                        -> status XML
      - GET /api/?Function=StartCountdown&Input=1&SelectedName=Time.Text
    """

    def __init__(
        self,
        host: str = "127.0.0.1",
        port: int = 8088,
        password: Optional[str] = None,
        timeout: float = 3.0
    ):
        self.host = host
        self.port = port
        self.password = password
        self.timeout = timeout

    @property
    def base_url(self) -> str:
        return f"http://{self.host}:{self.port}"

    def _build_url(self, path: str = "/api/", params: Optional[dict] = None) -> str:
        if not path.startswith("/"):
            path = "/" + path
        url = self.base_url + path
        if params:
            qs = urllib.parse.urlencode(params)
            url = url + "?" + qs
        return url

    def _http_get(self, url: str) -> str:
        req = urllib.request.Request(url, method="GET")
        try:
            with urllib.request.urlopen(req, timeout=self.timeout) as resp:
                return resp.read().decode("utf-8", errors="replace")
        except (urllib.error.URLError, socket.timeout) as e:
            raise RuntimeError(f"vMix HTTP error: {e}") from e

    # ========================================
    # Status XML
    # ========================================
    def get_status_xml(self) -> ET.Element:
        """
        Fetch vMix XML (/api/) and return root element.
        """
        url = self._build_url("/api/")
        text = self._http_get(url)
        try:
            root = ET.fromstring(text)
        except ET.ParseError as e:
            raise RuntimeError(f"Failed to parse vMix XML: {e}") from e
        return root

    # ========================================
    # Input Discovery
    # ========================================
    def find_input_number(self, name_or_number: str | int) -> Optional[str]:
        """
        Takes either a number (1, '1') or a title/shortTitle
        and returns the input number as string, or None if not found.
        """
        if isinstance(name_or_number, int):
            return str(name_or_number)
        s = str(name_or_number).strip()
        if s.isdigit():
            return s

        root = self.get_status_xml()
        inputs = root.findall("./inputs/input")
        s_lower = s.lower()

        for inp in inputs:
            num = inp.get("number")
            title = (inp.get("title") or "").strip()
            short_title = (inp.get("shortTitle") or "").strip()
            key = (inp.get("key") or "").strip()

            if (
                title.lower() == s_lower
                or short_title.lower() == s_lower
                or key.lower() == s_lower
            ):
                return num
        return None

    def _find_input_node(self, name_or_number: str | int) -> Optional[ET.Element]:
        num = self.find_input_number(name_or_number)
        if num is None:
            return None
        root = self.get_status_xml()
        for inp in root.findall("./inputs/input"):
            if inp.get("number") == num:
                return inp
        return None

    # ========================================
    # Text Field Access
    # ========================================
    def get_text_field(
        self,
        input_name_or_number: str | int,
        field_name: str
    ) -> str:
        """
        Get text from a Title text field.
        """
        node = self._find_input_node(input_name_or_number)
        if node is None:
            return ""
        for txt in node.findall("./text"):
            if (txt.get("name") or "") == field_name:
                return (txt.text or "").strip()
        return ""

    # ========================================
    # Commands
    # ========================================
    def set_text(
        self,
        input_name_or_number: str | int,
        field_name: str,
        value: str
    ) -> None:
        """
        Set text in Title field via Function=SetText.
        """
        inp_num = self.find_input_number(input_name_or_number)
        if inp_num is None:
            raise ValueError(f"Input not found: {input_name_or_number}")

        self.call_function(
            "SetText",
            Input=inp_num,
            SelectedName=field_name,
            Value=str(value),
        )

    def set_countdown(
        self,
        input_name_or_number: str | int,
        field_name: str,
        value: str
    ) -> None:
        """
        Set vMix internal countdown value (start time) in a field.
        Example: '20:00'.
        """
        inp_num = self.find_input_number(input_name_or_number)
        if inp_num is None:
            raise ValueError(f"Input not found: {input_name_or_number}")

        self.call_function(
            "SetCountdown",
            Input=inp_num,
            SelectedName=field_name,
            Value=str(value),
        )

    def call_function(self, function_name: str, **params) -> None:
        """
        Execute a vMix Function, e.g.:
          call_function("StartCountdown", Input=1, SelectedName="Time.Text")
        """
        q = {"Function": function_name}
        for k, v in params.items():
            if v is None:
                continue
            q[k] = str(v)

        url = self._build_url("/api/", q)
        _ = self._http_get(url)

    # ========================================
    # Overlay Helpers
    # ========================================
    def overlay_on(
        self,
        input_name_or_number: str | int,
        channel: int = 1
    ) -> None:
        """
        Turn on input as overlay on given channel (1-8).
        """
        inp_num = self.find_input_number(input_name_or_number)
        if inp_num is None:
            raise ValueError(f"Input not found: {input_name_or_number}")
        func = f"OverlayInput{int(channel)}In"
        self.call_function(func, Input=inp_num)

    def overlay_off(
        self,
        input_name_or_number: str | int,
        channel: int = 1
    ) -> None:
        """
        Turn off input from overlay on given channel (1-8).
        """
        inp_num = self.find_input_number(input_name_or_number)
        if inp_num is None:
            raise ValueError(f"Input not found: {input_name_or_number}")
        func = f"OverlayInput{int(channel)}Out"
        self.call_function(func, Input=inp_num)

    # ========================================
    # Visibility Helpers
    # ========================================
    def set_text_visible(
        self,
        input_name_or_number: str | int,
        field_name: str,
        visible: bool
    ) -> None:
        """
        SetTextVisibleOn/Off for a text field.
        """
        inp_num = self.find_input_number(input_name_or_number)
        if inp_num is None:
            raise ValueError(f"Input not found: {input_name_or_number}")
        
        func = "SetTextVisibleOn" if visible else "SetTextVisibleOff"
        self.call_function(func, Input=inp_num, SelectedName=field_name)

    def set_image_visible(
        self,
        input_name_or_number: str | int,
        field_name: str,
        visible: bool
    ) -> None:
        """
        SetImageVisibleOn/Off for an image field.
        """
        inp_num = self.find_input_number(input_name_or_number)
        if inp_num is None:
            raise ValueError(f"Input not found: {input_name_or_number}")
        
        func = "SetImageVisibleOn" if visible else "SetImageVisibleOff"
        self.call_function(func, Input=inp_num, SelectedName=field_name)