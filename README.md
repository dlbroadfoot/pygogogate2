# pygogogate2 
Python wrapper for Gogogate2 API
=======

[![Build Status](https://travis-ci.org/dlbroadfoot/pygogogate2.svg?branch=master)](https://travis-ci.org/dlbroadfoot/pygogogate2)

# Introduction

This is a python module aiming to interact with the Gogogate2 API.

Code is licensed under the MIT license.

Getting Started
===============

# Usage

```python
from pygogogate2 import Gogogate2API as pygogogate2

gogate2 = pygogogate2(username, password, brand)
```

# Methods

def get_devices(self):
"""Return devices from API"""
       
def get_status(self, device_id):
"""Return current door status(open/closed)"""

def close_device(self, device_id):
"""Send request to close the door."""

def open_device(self, device_id):
"""Send request to open the door."""

### Disclaimer

The code here is based off of an unsupported API from [Gogogate2](https://www.gogogate.com/) and is subject to change without notice. The authors claim no responsibility for damages to your garage door or property by use of the code within.
