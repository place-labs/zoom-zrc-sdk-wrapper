 #!/usr/bin/env python3
"""
Sink contract test (runs in the built image).

For every callback the C++ trampolines forward to Python, this harness fabricates
the SDK struct / enum / primitive arguments, invokes the matching Python sink
method with a capturing manager, and asserts the emitted WebSocket payload:
  - is produced exactly once,
  - is JSON-serializable (catches binary/enum/field-name problems),
  - carries an "event" key.

It exercises the payload-serialization layer (`_pybind_to_jsonable`, field names,
enum conversion) for ALL forwarded events — including ones that can only occur in
a live meeting — with no Zoom Room and no running event loop.

The set of callbacks + their argument types is derived by parsing the trampolines
in bindings/zrc_bindings.cpp, so it stays in sync automatically.

Run inside the built image:
  docker run --rm -v "$PWD/service/test_sink_contracts.py:/app/service/test_sink_contracts.py" \
    --entrypoint python zrc-build-check /app/service/test_sink_contracts.py
"""
import json
import os
import re
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import zrc_sdk          # noqa: E402
import room_manager as rm  # noqa: E402

BINDINGS = os.environ.get("ZRC_BINDINGS", "/app/bindings/zrc_bindings.cpp")

PRIMITIVES = {
    "bool": True, "int": 1, "int32_t": 1, "int64_t": 1, "uint32_t": 1,
    "uint64_t": 1, "float": 1.0, "double": 1.0, "std::string": "test",
    "time_t": 0, "size_t": 1,
}


class Capture:
    def __init__(self):
        self.events = []

    def broadcast_event(self, room_id, payload):
        json.dumps(payload)          # raises if the payload isn't serializable
        self.events.append(payload)

    # Connection-management hooks some sinks also call on the manager
    # (auto-reconnect). No-ops here so the contract test stays focused on the
    # emitted payload rather than reconnect side effects.
    def mark_unpaired(self, *args, **kwargs):
        pass

    def schedule_reconnect(self, *args, **kwargs):
        pass

    def cancel_reconnect(self, *args, **kwargs):
        pass


def split_params(params):
    out, depth, cur = [], 0, ""
    for ch in params:
        if ch == "<":
            depth += 1
        elif ch == ">":
            depth -= 1
        if ch == "," and depth == 0:
            out.append(cur)
            cur = ""
        else:
            cur += ch
    if cur.strip():
        out.append(cur)
    return out


def param_type(part):
    part = re.sub(r"\s+\w+\s*$", "", part.strip())      # drop the parameter name
    return part.replace("const", "").replace("&", "").strip()


def parse_forwarded(src):
    """[(attr_name, [cpp_type, ...]), ...] for every trampoline method that forwards.

    Each method body is delimited by brace-balancing from its opening `{`, so a
    method's parameters are always paired with its own forwarded attr name.
    """
    results = []
    for m in re.finditer(r"void\s+\w+\(([^)]*)\)\s*override\s*\{", src):
        params = m.group(1)
        depth, i = 0, m.end() - 1
        while i < len(src):
            if src[i] == "{":
                depth += 1
            elif src[i] == "}":
                depth -= 1
                if depth == 0:
                    break
            i += 1
        body = src[m.end():i]
        am = re.search(r'py_sink\.attr\("(\w+)"\)', body)
        if not am:
            continue                                     # no-op stub, not forwarded
        types = [param_type(p) for p in split_params(params.strip())] if params.strip() else []
        results.append((am.group(1), types))
    return results


def sample(cpp_type):
    t = cpp_type.strip()
    if t in PRIMITIVES:
        return PRIMITIVES[t]
    vm = re.match(r"std::vector<(.+)>$", t)
    if vm:
        return [sample(vm.group(1))]
    name = t.split("::")[-1]
    obj = getattr(zrc_sdk, name, None)
    if obj is None:
        raise KeyError(f"unbound type '{t}'")
    if hasattr(obj, "__members__"):                      # pybind enum
        return list(obj.__members__.values())[0]
    return obj()                                         # struct: default-construct


def sink_class_for(attr):
    for name in dir(rm):
        cls = getattr(rm, name)
        if (isinstance(cls, type) and issubclass(cls, rm._Broadcaster)
                and cls is not rm._Broadcaster and attr in cls.__dict__):
            return cls
    return None


def main():
    forwarded = parse_forwarded(open(BINDINGS).read())
    passed, failed, errors = [], [], []

    for attr, types in forwarded:
        cls = sink_class_for(attr)
        if cls is None:
            errors.append((attr, "no Python sink method forwards this callback"))
            continue
        try:
            args = [sample(t) for t in types]
        except Exception as e:                           # noqa: BLE001
            errors.append((attr, f"could not build fixture: {e}"))
            continue
        inst = cls("contract-test-room")
        inst.mgr = Capture()
        try:
            getattr(inst, attr)(*args)
        except Exception as e:                           # noqa: BLE001
            failed.append((attr, f"emit raised {type(e).__name__}: {e}"))
            continue
        evs = inst.mgr.events
        if len(evs) != 1:
            failed.append((attr, f"produced {len(evs)} events, expected 1"))
        elif "event" not in evs[0]:
            failed.append((attr, "payload missing 'event' key"))
        else:
            passed.append(attr)

    print("\n===== Sink contract test =====")
    print(f"forwarded callbacks discovered : {len(forwarded)}")
    print(f"PASS                           : {len(passed)}")
    print(f"FAIL                           : {len(failed)}")
    print(f"ERROR (fixture/coverage)       : {len(errors)}")
    for a, e in failed:
        print(f"  ✗ FAIL  {a}: {e}")
    for a, e in errors:
        print(f"  ! ERROR {a}: {e}")
    print()
    return 1 if (failed or errors) else 0


if __name__ == "__main__":
    sys.exit(main())
