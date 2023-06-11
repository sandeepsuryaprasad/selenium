# Licensed to the Software Freedom Conservancy (SFC) under one
# or more contributor license agreements.  See the NOTICE file
# distributed with this work for additional information
# regarding copyright ownership.  The SFC licenses this file
# to you under the Apache License, Version 2.0 (the
# "License"); you may not use this file except in compliance
# with the License.  You may obtain a copy of the License at
#
#   http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing,
# software distributed under the License is distributed on an
# "AS IS" BASIS, WITHOUT WARRANTIES OR CONDITIONS OF ANY
# KIND, either express or implied.  See the License for the
# specific language governing permissions and limitations
# under the License.

"""The Proxy implementation."""


class ProxyTypeFactory:
    @staticmethod
    def make(ff_value, string):
        return {"ff_value": ff_value, "string": string}


class ProxyType:
    """Set of possible types of proxy.

    Each proxy type has 2 properties:    'ff_value' is value of Firefox
    profile preference,    'string' is id of proxy type.
    """

    DIRECT = ProxyTypeFactory.make(0, "DIRECT")  # Direct connection, no proxy (default on Windows).
    MANUAL = ProxyTypeFactory.make(1, "MANUAL")  # Manual proxy settings (e.g., for httpProxy).
    PAC = ProxyTypeFactory.make(2, "PAC")  # Proxy autoconfiguration from URL.
    RESERVED_1 = ProxyTypeFactory.make(3, "RESERVED1")  # Never used.
    AUTODETECT = ProxyTypeFactory.make(4, "AUTODETECT")  # Proxy autodetection (presumably with WPAD).
    SYSTEM = ProxyTypeFactory.make(5, "SYSTEM")  # Use system settings (default on Linux).
    UNSPECIFIED = ProxyTypeFactory.make(6, "UNSPECIFIED")  # Not initialized (for internal use).

    @classmethod
    def load(cls, value):
        if isinstance(value, dict) and "string" in value:
            value = value["string"]
        value = str(value).upper()
        for attr in dir(cls):
            attr_value = getattr(cls, attr)
            if isinstance(attr_value, dict) and "string" in attr_value and attr_value["string"] == value:
                return attr_value
        raise Exception(f"No proxy type is found for {value}")


class ProxyDescriptor:
    """gets and sets proxyType on Proxy object."""

    def __set__(self, obj, value):
        getattr(obj, "_verify_proxy_type_compatibility")(value)
        setattr(type(obj), "proxyType", value)

    def __get__(self, obj, cls):
        return getattr(type(obj), "proxyType")


class ProxyTypeDescriptor:
    """gets and sets below attributes on Proxy object.

    - autodetect
    - ftpProxy
    - httpProxy
    - noProxy
    - proxyAutoconfigUrl
    - sslProxy
    - socksProxy
    - socksUsername
    - socksPassword
    - socksVersion
    """

    def __init__(self, name, p_type):
        self.name = name
        self.p_type = p_type

    def __get__(self, obj, cls):
        return getattr(type(obj), self.name)

    def __set__(self, obj, value):
        if self.name == "autodetect" and not isinstance(value, bool):
            raise ValueError("Autodetect proxy value needs to be a boolean")
        getattr(obj, "_verify_proxy_type_compatibility")(self.p_type)
        setattr(type(obj), "proxyType", self.p_type)
        setattr(type(obj), self.name, value)


class Proxy:
    """Proxy contains information about proxy type and necessary proxy
    settings."""

    proxyType = ProxyType.UNSPECIFIED
    autodetect = False
    ftpProxy = ""
    httpProxy = ""
    noProxy = ""
    proxyAutoconfigUrl = ""
    sslProxy = ""
    socksProxy = ""
    socksUsername = ""
    socksPassword = ""
    socksVersion = None

    # Creating Descriptor objects
    proxy_type = ProxyDescriptor()
    auto_detect = ProxyTypeDescriptor("autodetect", ProxyType.AUTODETECT)
    ftp_proxy = ProxyTypeDescriptor("ftpProxy", ProxyType.MANUAL)
    http_proxy = ProxyTypeDescriptor("httpProxy", ProxyType.MANUAL)
    no_proxy = ProxyTypeDescriptor("noProxy", ProxyType.MANUAL)
    proxy_autoconfig_url = ProxyTypeDescriptor("proxyAutoconfigUrl", ProxyType.PAC)
    ssl_proxy = ProxyTypeDescriptor("sslProxy", ProxyType.MANUAL)
    socks_proxy = ProxyTypeDescriptor("socksProxy", ProxyType.MANUAL)
    socks_username = ProxyTypeDescriptor("socksUsername", ProxyType.MANUAL)
    socks_password = ProxyTypeDescriptor("socksPassword", ProxyType.MANUAL)
    socks_version = ProxyTypeDescriptor("socksVersion", ProxyType.MANUAL)

    def __init__(self, raw=None):
        """Creates a new Proxy.

        :Args:
         - raw: raw proxy data. If None, default class values are used.
        """

        if raw:
            if "proxyType" in raw and raw["proxyType"]:
                self.proxy_type = ProxyType.load(raw["proxyType"])
            if "ftpProxy" in raw and raw["ftpProxy"]:
                self.ftp_proxy = raw["ftpProxy"]
            if "httpProxy" in raw and raw["httpProxy"]:
                self.http_proxy = raw["httpProxy"]
            if "noProxy" in raw and raw["noProxy"]:
                self.no_proxy = raw["noProxy"]
            if "proxyAutoconfigUrl" in raw and raw["proxyAutoconfigUrl"]:
                self.proxy_autoconfig_url = raw["proxyAutoconfigUrl"]
            if "sslProxy" in raw and raw["sslProxy"]:
                self.sslProxy = raw["sslProxy"]
            if "autodetect" in raw and raw["autodetect"]:
                self.auto_detect = raw["autodetect"]
            if "socksProxy" in raw and raw["socksProxy"]:
                self.socks_proxy = raw["socksProxy"]
            if "socksUsername" in raw and raw["socksUsername"]:
                self.socks_username = raw["socksUsername"]
            if "socksPassword" in raw and raw["socksPassword"]:
                self.socks_password = raw["socksPassword"]
            if "socksVersion" in raw and raw["socksVersion"]:
                self.socks_version = raw["socksVersion"]

    def _verify_proxy_type_compatibility(self, compatible_proxy):
        if self.proxyType not in (ProxyType.UNSPECIFIED, compatible_proxy):
            raise Exception(f"Specified proxy type ({compatible_proxy}) not with current settings ({self.proxyType}")

    def to_capabilities(self):
        proxy_caps = {"proxyType": self.proxyType["string"].lower()}
        proxies = [
            "autodetect",
            "ftpProxy",
            "httpProxy",
            "proxyAutoconfigUrl",
            "sslProxy",
            "noProxy",
            "socksProxy",
            "socksUsername",
            "socksPassword",
            "socksVersion",
        ]
        for proxy in proxies:
            attr_value = getattr(self, proxy)
            if attr_value:
                proxy_caps[proxy] = attr_value
        return proxy_caps
