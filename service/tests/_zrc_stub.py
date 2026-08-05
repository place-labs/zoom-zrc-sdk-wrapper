"""
Test double for the compiled `zrc_sdk` module, for unit tests that exercise
service-layer logic (room_manager, controllers) without the C++ SDK.

Import this module BEFORE importing `room_manager` / `controllers.*`; it installs
a stub `zrc_sdk` into sys.modules and puts the service directory on sys.path.

`FakeService` mimics the SDK object graph: `Get*()`/`Create*()` return memoized
child nodes, `RegisterSink`/`DeregisterSink` succeed (return 0) and record calls,
and any other method returns 0.
"""
import os
import sys
import types

SERVICE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if SERVICE_DIR not in sys.path:
    sys.path.insert(0, SERVICE_DIR)


class FakeService:
    def __init__(self, name="root"):
        self._name = name
        self._children = {}
        self.registered = []      # sinks passed to RegisterSink
        self.deregistered = 0     # number of DeregisterSink calls

    def RegisterSink(self, sink):
        self.registered.append(sink)
        return 0  # ZRCSDKERR_SUCCESS

    def DeregisterSink(self, *args):
        self.deregistered += 1
        return 0

    def __getattr__(self, attr):
        if attr.startswith("_"):
            raise AttributeError(attr)
        if attr.startswith("Get") or attr.startswith("Create"):
            child = self._children.setdefault(attr, FakeService(attr))
            return lambda *a, **k: child
        return lambda *a, **k: 0

    def walk(self):
        """Yield this node and every child node reachable via Get*/Create* calls."""
        yield self
        for child in self._children.values():
            yield from child.walk()


def _install():
    stub = types.ModuleType("zrc_sdk")
    stub.ZRCSDKERR_SUCCESS = 0
    stub.ZRCSDKERR_INTERNAL_ERROR = 7
    stub.CreateInstanceWithSink = lambda sink: FakeService("sdk")

    def _module_getattr(name):
        # Enum/constant accesses resolve to a memoized placeholder so equality
        # comparisons against the same attribute are stable.
        placeholder = types.SimpleNamespace(name=name)
        setattr(stub, name, placeholder)
        return placeholder

    stub.__getattr__ = _module_getattr
    sys.modules["zrc_sdk"] = stub
    return stub


zrc_sdk = sys.modules.get("zrc_sdk") or _install()
