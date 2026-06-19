from app.core.event_bus import EventBus


def test_event_bus_emit_calls_listener():
    bus = EventBus()
    received_payloads = []

    def listener(payload):
        received_payloads.append(payload)

    bus.subscribe("TEST_EVENT", listener)
    bus.emit("TEST_EVENT", {"value": 123})

    assert len(received_payloads) == 1
    assert received_payloads[0]["value"] == 123


def test_event_bus_without_payload():
    bus = EventBus()
    received_payloads = []

    def listener(payload):
        received_payloads.append(payload)

    bus.subscribe("TEST_EVENT", listener)
    bus.emit("TEST_EVENT")

    assert len(received_payloads) == 1
    assert received_payloads[0] == {}
