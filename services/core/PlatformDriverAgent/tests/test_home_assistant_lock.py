# -*- coding: utf-8 -*- {{{
# ===----------------------------------------------------------------------===
#
#                 Component of Eclipse VOLTTRON
#
# ===----------------------------------------------------------------------===
#
# Copyright 2025 Battelle Memorial Institute
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

import gevent
import pytest

from volttron.platform import get_services_core
from volttron.platform.agent import utils
from volttron.platform.agent.known_identities import PLATFORM_DRIVER, CONFIGURATION_STORE
from volttrontesting.utils.platformwrapper import PlatformWrapper

utils.setup_logging()
logger = logging.getLogger(__name__)

# These values should point to a running Home Assistant instance and a real lock entity.
# Example values assume a local Home Assistant at http://127.0.0.1:8123 and a lock entity
# called "lock.front_door". Replace ACCESS_TOKEN and LOCK_ENTITY_ID with values that exist
# in your environment before running these tests.
HOMEASSISTANT_TEST_IP = "127.0.0.1"
ACCESS_TOKEN = "YOUR_LONG_LIVED_ACCESS_TOKEN"
PORT = "8123"
LOCK_ENTITY_ID = "lock.front_door"  # e.g. "lock.front_door"

skip_msg = (
    "Some configuration variables are not set. "
    "Check HOMEASSISTANT_TEST_IP, ACCESS_TOKEN, PORT, and LOCK_ENTITY_ID"
)

pytestmark = pytest.mark.skipif(
    not (HOMEASSISTANT_TEST_IP and ACCESS_TOKEN and PORT and LOCK_ENTITY_ID),
    reason=skip_msg,
)

HOMEASSISTANT_LOCK_DEVICE_TOPIC = "devices/home_assistant_lock"


def test_lock_set_and_read_back(volttron_instance: PlatformWrapper, lock_config_store):
    """
    Integration test that writes to a Home Assistant smart lock and reads the value
    back through scrape_all.
    """
    agent = volttron_instance.dynamic_agent

    # Lock the device (1)
    agent.vip.rpc.call(PLATFORM_DRIVER, "set_point", "home_assistant_lock", "lock_state", 1).get(timeout=20)
    gevent.sleep(10)
    result = agent.vip.rpc.call(PLATFORM_DRIVER, "scrape_all", "home_assistant_lock").get(timeout=20)
    assert result.get("lock_state") in (1, "locked"), "Expected locked state after commanding 1"

    # Unlock the device (0)
    agent.vip.rpc.call(PLATFORM_DRIVER, "set_point", "home_assistant_lock", "lock_state", 0).get(timeout=20)
    gevent.sleep(10)
    result = agent.vip.rpc.call(PLATFORM_DRIVER, "scrape_all", "home_assistant_lock").get(timeout=20)
    assert result.get("lock_state") in (0, "unlocked"), "Expected unlocked state after commanding 0"


@pytest.fixture(scope="module")
def lock_config_store(volttron_instance: PlatformWrapper, platform_driver_lock):
    capabilities = [{"edit_config_store": {"identity": PLATFORM_DRIVER}}]
    volttron_instance.add_capabilities(volttron_instance.dynamic_agent.core.publickey, capabilities)

    registry_config = "homeassistant_lock_test.json"
    registry_obj = [
        {
            "Entity ID": LOCK_ENTITY_ID,
            "Entity Point": "state",
            "Volttron Point Name": "lock_state",
            "Units": "Enumeration",
            "Units Details": "0: unlocked, 1: locked",
            "Writable": True,
            "Starting Value": 0,
            "Type": "int",
            "Notes": "Smart lock used for integration testing",
        }
    ]

    volttron_instance.dynamic_agent.vip.rpc.call(
        CONFIGURATION_STORE,
        "manage_store",
        PLATFORM_DRIVER,
        registry_config,
        json.dumps(registry_obj),
        config_type="json",
    )
    gevent.sleep(2)

    driver_config = {
        "driver_config": {
            "ip_address": HOMEASSISTANT_TEST_IP,
            "access_token": ACCESS_TOKEN,
            "port": PORT,
        },
        "driver_type": "home_assistant",
        "registry_config": f"config://{registry_config}",
        "timezone": "US/Pacific",
        "interval": 30,
    }

    volttron_instance.dynamic_agent.vip.rpc.call(
        CONFIGURATION_STORE,
        "manage_store",
        PLATFORM_DRIVER,
        HOMEASSISTANT_LOCK_DEVICE_TOPIC,
        json.dumps(driver_config),
        config_type="json",
    )
    gevent.sleep(2)

    yield platform_driver_lock

    logger.info("Wiping out store for lock tests.")
    volttron_instance.dynamic_agent.vip.rpc.call(CONFIGURATION_STORE, "manage_delete_store", PLATFORM_DRIVER)
    gevent.sleep(0.1)


@pytest.fixture(scope="module")
def platform_driver_lock(volttron_instance: PlatformWrapper):
    platform_uuid = volttron_instance.install_agent(
        agent_dir=get_services_core("PlatformDriverAgent"),
        config_file={
            "publish_breadth_first_all": False,
            "publish_depth_first": False,
            "publish_breadth_first": False,
        },
        start=True,
    )
    gevent.sleep(2)
    assert volttron_instance.is_agent_running(platform_uuid)
    yield platform_uuid

    volttron_instance.stop_agent(platform_uuid)
    if not volttron_instance.debug_mode:
        volttron_instance.remove_agent(platform_uuid)


