export const meta = {
  name: 'sink-audit',
  description: 'Cross-check every sink surface across bindings, registration, cleanup, and test coverage',
  whenToUse: 'After adding/changing sinks or upgrading the SDK — catches drift between the hand-maintained mirrors (bindings, register_sinks_for_room, _deregister_room_sinks, test_sink_lifecycle surfaces()).',
  phases: [
    { title: 'Enumerate', detail: 'list every sink surface from the bindings' },
    { title: 'Audit', detail: 'one agent per surface, checks all five mirrors' },
    { title: 'Report', detail: 'collect mismatches' },
  ],
}

const SURFACES_SCHEMA = {
  type: 'object',
  required: ['surfaces'],
  properties: {
    surfaces: {
      type: 'array',
      items: {
        type: 'object',
        required: ['iface', 'trampoline'],
        properties: {
          iface: { type: 'string', description: 'C++ interface, e.g. IMeetingService' },
          trampoline: { type: 'string', description: 'trampoline class name' },
        },
      },
    },
  },
}

const AUDIT_SCHEMA = {
  type: 'object',
  required: ['iface', 'ok', 'problems'],
  properties: {
    iface: { type: 'string' },
    ok: { type: 'boolean' },
    problems: { type: 'array', items: { type: 'string' } },
  },
}

phase('Enumerate')
const { surfaces } = await agent(
  `In bindings/zrc_bindings.cpp, find every interface that has a RegisterSink/DeregisterSink
lambda pair (grep for 'SinkRegistry<'). Return each interface name and its trampoline class.
Return raw data only.`,
  { label: 'enumerate-surfaces', schema: SURFACES_SCHEMA }
)
log(`${surfaces.length} sink surfaces found`)

phase('Audit')
const results = await parallel(surfaces.map(s => () =>
  agent(
    `Audit the sink surface ${s.iface} (trampoline ${s.trampoline}) in this repo for drift
across its five hand-maintained mirrors. Check each and report a problem string for any miss:

1. bindings/zrc_bindings.cpp: BOTH the RegisterSink and DeregisterSink lambdas for ${s.iface}
   use the shared SinkRegistry<${s.iface}, ${s.trampoline}>() — no lambda-local static maps.
   Every trampoline callback acquires the GIL before touching Python.
2. generator/templates/zrc_bindings.cpp is byte-identical for this surface's code.
3. service/room_manager.py: a Python sink class exists for it, a store dict ending in
   '_sinks' exists in RoomManager.__init__, and register_sinks_for_room registers it
   (sink.mgr set, success checked, stored).
4. service/room_manager.py: _deregister_room_sinks' surfaces() generator yields this surface.
5. service/test_sink_lifecycle.py: its surfaces() generator yields this surface.

(Exception: the top-level IZRCSDK sink and helpers intentionally not wired — say so instead
of flagging.) Return raw data: iface, ok, problems[].`,
    { label: `audit:${s.iface}`, schema: AUDIT_SCHEMA, agentType: 'bindings-auditor' }
  )
))

phase('Report')
const audited = results.filter(Boolean)
const drifted = audited.filter(r => !r.ok)
log(`${audited.length} audited, ${drifted.length} with drift`)
return {
  total: audited.length,
  clean: audited.length - drifted.length,
  drift: drifted,
}
