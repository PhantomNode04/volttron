# -*- coding: utf-8 -*- {{{
# ===----------------------------------------------------------------------===
#
#                 Component of Eclipse VOLTTRON
#
# ===----------------------------------------------------------------------===
#
# Copyright 2023 Battelle Memorial Institute
#
# Licensed under the Apache License, Version 2.0 (the "License"); you may not
# use this file except in compliance with the License. You may obtain a copy
# of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS, WITHOUT
# WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied. See the
# License for the specific language governing permissions and limitations
# under the License.
#
# ===----------------------------------------------------------------------===
# }}}

import json
import logging
import pytest
import gevent

from volttron.platform.agent.known_identities import (
    PLATFORM_DRIVER,
    CONFIGURATION_STORE,
)
from volttron.platform import get_services_core
from volttron.platform.agent import utils
from volttron.platform.keystore import KeyStore
from volttrontesting.utils.platformwrapper import PlatformWrapper

utils.setup_logging()
logger = logging.getLogger(__name__)

# To run these tests, create a helper toggle named volttrontest in your Home Assistant instance.
# This can be done by going to Settings > Devices & services > Helpers > Create Helper > Toggle
HOMEASSISTANT_TEST_IP = ""
ACCESS_TOKEN = ""
PORT = ""

skip_msg = "Some configuration variables are not set. Check HOMEASSISTANT_TEST_IP, ACCESS_TOKEN, and PORT"

# Skip tests if variables are not set
pytestmark = pytest.mark.skipif(
    not (HOMEASSISTANT_TEST_IP and ACCESS_TOKEN and PORT),
    reason=skip_msg
)
HOMEASSISTANT_DEVICE_TOPIC = "devices/home_assistant"


# Get the point which will should be off
def test_get_point(volttron_instance, config_store):
    expected_values = 0
    agent = volttron_instance.dynamic_agent
    result = agent.vip.rpc.call(PLATFORM_DRIVER, 'get_point', 'home_assistant', 'bool_state').get(timeout=20)
    assert result == expected_values, "The result does not match the expected result."


# The default value for this fake light is 3. If the test cannot reach out to home assistant,
# the value will default to 3 making the test fail.
def test_data_poll(volttron_instance: PlatformWrapper, config_store):
    expected_values = [{'bool_state': 0}, {'bool_state': 1}]
    agent = volttron_instance.dynamic_agent
    result = agent.vip.rpc.call(PLATFORM_DRIVER, 'scrape_all', 'home_assistant').get(timeout=20)
    assert result in expected_values, "The result does not match the expected result."


# Turn on the light. Light is automatically turned off every 30 seconds to allow test to turn
# it on and receive the correct value.
def test_set_point(volttron_instance, config_store):
    expected_values = {'bool_state': 1}
    agent = volttron_instance.dynamic_agent
    agent.vip.rpc.call(PLATFORM_DRIVER, 'set_point', 'home_assistant', 'bool_state', 1)
    gevent.sleep(10)
    result = agent.vip.rpc.call(PLATFORM_DRIVER, 'scrape_all', 'home_assistant').get(timeout=20)
    assert result == expected_values, "The result does not match the expected result."

# New tests 

def test_lock_state(volttron_instance, config_store):
    """Test locking and unlocking the front door."""
    agent = volttron_instance.dynamic_agent

    # Lock (1)
    agent.vip.rpc.call(PLATFORM_DRIVER, 'set_point',
                       'home_assistant', 'front_door_lock_state', 1)
    gevent.sleep(10)

    result = agent.vip.rpc.call(PLATFORM_DRIVER, 'scrape_all',
                                'home_assistant').get(timeout=20)

    assert result.get('front_door_lock_state') in (1, "locked")

    # Unlock (0)
    agent.vip.rpc.call(PLATFORM_DRIVER, 'set_point',
                       'home_assistant', 'front_door_lock_state', 0)
    gevent.sleep(10)

    result = agent.vip.rpc.call(PLATFORM_DRIVER, 'scrape_all',
                                'home_assistant').get(timeout=20)

    assert result.get('front_door_lock_state') in (0, "unlocked")

def test_lock_string_inputs(volttron_instance, config_store):
    """Test lock command normalization for various string inputs."""
    agent = volttron_instance.dynamic_agent

    # Locked → lock → expect 1
    agent.vip.rpc.call(
        PLATFORM_DRIVER, "set_point",
        "home_assistant", "front_door_lock_state", "locked"
    )
    gevent.sleep(10)
    result = agent.vip.rpc.call(
        PLATFORM_DRIVER, "scrape_all", "home_assistant"
    ).get(timeout=20)
    assert result.get("front_door_lock_state") in (1, "locked")

    # Open → unlock → expect 0
    agent.vip.rpc.call(
        PLATFORM_DRIVER, "set_point",
        "home_assistant", "front_door_lock_state", "open"
    )
    gevent.sleep(10)
    result = agent.vip.rpc.call(
        PLATFORM_DRIVER, "scrape_all", "home_assistant"
    ).get(timeout=20)
    assert result.get("front_door_lock_state") in (0, "unlocked")

    # "false" → unlock → expect 0
    agent.vip.rpc.call(
        PLATFORM_DRIVER, "set_point",
        "home_assistant", "front_door_lock_state", "false"
    )
    gevent.sleep(10)
    result = agent.vip.rpc.call(
        PLATFORM_DRIVER, "scrape_all", "home_assistant"
    ).get(timeout=20)
    assert result.get("front_door_lock_state") in (0, "unlocked")

    # "lock" → lock → expect 1
    agent.vip.rpc.call(
        PLATFORM_DRIVER, "set_point",
        "home_assistant", "front_door_lock_state", "lock"
    )
    gevent.sleep(10)
    result = agent.vip.rpc.call(
        PLATFORM_DRIVER, "scrape_all", "home_assistant"
    ).get(timeout=20)
    assert result.get("front_door_lock_state") in (1, "locked")


def test_fan_switch(volttron_instance, config_store):
    """Test turning the fan on and off."""
    agent = volttron_instance.dynamic_agent

    # Turn ON
    agent.vip.rpc.call(PLATFORM_DRIVER, 'set_point',
                       'home_assistant', 'living_room_fan_state', 1)
    gevent.sleep(10)

    result = agent.vip.rpc.call(PLATFORM_DRIVER, 'scrape_all',
                                'home_assistant').get(timeout=20)

    assert result.get('living_room_fan_state') in (1, "on")

    # Turn OFF
    agent.vip.rpc.call(PLATFORM_DRIVER, 'set_point',
                       'home_assistant', 'living_room_fan_state', 0)
    gevent.sleep(10)

    result = agent.vip.rpc.call(PLATFORM_DRIVER, 'scrape_all',
                                'home_assistant').get(timeout=20)

    assert result.get('living_room_fan_state') in (0, "off")


def test_fan_percentage(volttron_instance, config_store):
    """Test setting the fan speed percentage."""
    agent = volttron_instance.dynamic_agent

    # Set fan to 50%
    agent.vip.rpc.call(PLATFORM_DRIVER, 'set_point',
                       'home_assistant', 'living_room_fan_percentage', 50)
    gevent.sleep(10)

    result = agent.vip.rpc.call(PLATFORM_DRIVER, 'scrape_all',
                                'home_assistant').get(timeout=20)

    pct = result.get('living_room_fan_percentage')

    # Some HA setups return int, some return string
    assert str(pct) in ("50", "50.0", "50")

def test_cover_open_close(volttron_instance, config_store):
    """Test opening and closing the curtain/cover."""
    agent = volttron_instance.dynamic_agent

    # Open cover
    agent.vip.rpc.call(
        PLATFORM_DRIVER, "set_point",
        "home_assistant", "curtain_state", 1
    )
    gevent.sleep(10)
    result = agent.vip.rpc.call(
        PLATFORM_DRIVER, "scrape_all", "home_assistant"
    ).get(timeout=20)

    assert result.get("curtain_state") in (1, "open")

    # Close cover
    agent.vip.rpc.call(
        PLATFORM_DRIVER, "set_point",
        "home_assistant", "curtain_state", 0
    )
    gevent.sleep(10)
    result = agent.vip.rpc.call(
        PLATFORM_DRIVER, "scrape_all", "home_assistant"
    ).get(timeout=20)

    assert result.get("curtain_state") in (0, "closed")

def test_cover_position(volttron_instance, config_store):
    """Test setting the curtain/cover position."""
    agent = volttron_instance.dynamic_agent

    # Set position to 50%
    agent.vip.rpc.call(
        PLATFORM_DRIVER,
        "set_point",
        "home_assistant",
        "curtain_position",
        50,
    ).get(timeout=20)

    gevent.sleep(10)

    result = agent.vip.rpc.call(
        PLATFORM_DRIVER,
        "scrape_all",
        "home_assistant",
    ).get(timeout=20)

    pos = result.get("curtain_position")

    assert str(pos) in ("50", "50.0")

def test_cover_position_invalid_input(volttron_instance, config_store):
    """Test that invalid cover position values raise errors or get clamped."""
    agent = volttron_instance.dynamic_agent

    # 1) Invalid string input should raise ValueError
    with pytest.raises(ValueError):
        agent.vip.rpc.call(
            PLATFORM_DRIVER,
            "set_point",
            "home_assistant",
            "curtain_position",
            "abc"   # invalid
        ).get(timeout=20)

    # 2) Position above 100 should be clamped to 100
    agent.vip.rpc.call(
        PLATFORM_DRIVER,
        "set_point",
        "home_assistant",
        "curtain_position",
        200       # out of range
    ).get(timeout=20)

    gevent.sleep(10)

    result = agent.vip.rpc.call(
        PLATFORM_DRIVER, "scrape_all", "home_assistant"
    ).get(timeout=20)

    assert str(result.get("curtain_position")) in ("100", "100.0"), \
        "Cover position should clamp to 100 for values above 100"

    # 3) Position below 0 should be clamped to 0
    agent.vip.rpc.call(
        PLATFORM_DRIVER,
        "set_point",
        "home_assistant",
        "curtain_position",
        -50       # out of range
    ).get(timeout=20)

    gevent.sleep(10)

    result = agent.vip.rpc.call(
        PLATFORM_DRIVER, "scrape_all", "home_assistant"
    ).get(timeout=20)

    assert str(result.get("curtain_position")) in ("0", "0.0"), \
        "Cover position should clamp to 0 for values below 0"

@pytest.fixture(scope="module")
def config_store(volttron_instance, platform_driver):

    capabilities = [{"edit_config_store": {"identity": PLATFORM_DRIVER}}]
    volttron_instance.add_capabilities(volttron_instance.dynamic_agent.core.publickey, capabilities)

    registry_config = "homeassistant_test.json"
    registry_obj = [{
        "Entity ID": "input_boolean.volttrontest",
        "Entity Point": "state",
        "Volttron Point Name": "bool_state",
        "Units": "On / Off",
        "Units Details": "off: 0, on: 1",
        "Writable": True,
        "Starting Value": 3,
        "Type": "int",
        "Notes": "lights hallway"
    },{
        "Entity ID": "lock.front_door",
        "Entity Point": "state",
        "Volttron Point Name": "front_door_lock_state",
        "Units": "Locked/Unlocked",
        "Writable": True,
        "Starting Value": 0,
        "Type": "int",
        "Notes": "front door lock"
    },{
        "Entity ID": "fan.living_room",
        "Entity Point": "state",
        "Volttron Point Name": "living_room_fan_state",
        "Units": "On/Off",
        "Writable": True,
        "Starting Value": 0,
        "Type": "int",
        "Notes": "fan power"
    },{
        "Entity ID": "fan.living_room",
        "Entity Point": "percentage",
        "Volttron Point Name": "living_room_fan_percentage",
        "Units": "%",
        "Writable": True,
        "Starting Value": 0,
        "Type": "int",
        "Notes": "fan speed"
    },{
    "Entity ID": "cover.living_room_curtain",
    "Entity Point": "state",
    "Volttron Point Name": "curtain_state",
    "Units": "Open/Closed",
    "Writable": True,
    "Starting Value": 0,
    "Type": "int",
    "Notes": "curtain open/close"
    },{
        "Entity ID": "cover.living_room_curtain",
        "Entity Point": "position",
        "Volttron Point Name": "curtain_position",
        "Units": "%",
        "Writable": True,
        "Starting Value": 0,
        "Type": "int",
        "Notes": "curtain position"
    }]

    volttron_instance.dynamic_agent.vip.rpc.call(CONFIGURATION_STORE,
                                                 "manage_store",
                                                 PLATFORM_DRIVER,
                                                 registry_config,
                                                 json.dumps(registry_obj),
                                                 config_type="json")
    gevent.sleep(2)
    # driver config
    driver_config = {
        "driver_config": {"ip_address": HOMEASSISTANT_TEST_IP, "access_token": ACCESS_TOKEN, "port": PORT},
        "driver_type": "home_assistant",
        "registry_config": f"config://{registry_config}",
        "timezone": "US/Pacific",
        "interval": 30,
    }

    volttron_instance.dynamic_agent.vip.rpc.call(CONFIGURATION_STORE,
                                                 "manage_store",
                                                 PLATFORM_DRIVER,
                                                 HOMEASSISTANT_DEVICE_TOPIC,
                                                 json.dumps(driver_config),
                                                 config_type="json"
                                                 )
    gevent.sleep(2)

    yield platform_driver

    print("Wiping out store.")
    volttron_instance.dynamic_agent.vip.rpc.call(CONFIGURATION_STORE, "manage_delete_store", PLATFORM_DRIVER)
    gevent.sleep(0.1)


@pytest.fixture(scope="module")
def platform_driver(volttron_instance):
    # Start the platform driver agent which would in turn start the bacnet driver
    platform_uuid = volttron_instance.install_agent(
        agent_dir=get_services_core("PlatformDriverAgent"),
        config_file={
            "publish_breadth_first_all": False,
            "publish_depth_first": False,
            "publish_breadth_first": False,
        },
        start=True,
    )
    gevent.sleep(2)  # wait for the agent to start and start the devices
    assert volttron_instance.is_agent_running(platform_uuid)
    yield platform_uuid

    volttron_instance.stop_agent(platform_uuid)
    if not volttron_instance.debug_mode:
        volttron_instance.remove_agent(platform_uuid)
