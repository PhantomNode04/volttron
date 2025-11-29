from services.core.PlatformDriverAgent.platform_driver.interfaces.home_assistant import Interface


def test_normalize_lock_command_accepts_ints():
    interface = Interface()
    assert interface._normalize_lock_command(1) == "lock"
    assert interface._normalize_lock_command(0) == "unlock"


def test_normalize_lock_command_accepts_strings():
    interface = Interface()
    assert interface._normalize_lock_command("locked") == "lock"
    assert interface._normalize_lock_command("unlock") == "unlock"


def test_convert_lock_state_maps_known_values():
    interface = Interface()
    assert interface._convert_lock_state("locked") == 1
    assert interface._convert_lock_state("unlocked") == 0
    assert interface._convert_lock_state("jammed") == "jammed"

