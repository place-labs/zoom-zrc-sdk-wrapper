# PlaceOS Zoom ZRC driver API parity

Audit target: `drivers/zoom/zoom_zrc.cr` as of 2026-08-17. `{room_id}` is
the configured PlaceOS room identifier. All JSON requests use
`Content-Type: application/json`; all REST calls accept JSON responses.

FastAPI returns HTTP 422 for a missing/malformed required query or body field.
Room-scoped routes return HTTP 404 when the room (or a required helper on some
recording routes) is absent. Unless a row says otherwise, an unexpected Python
or SDK invocation exception returns HTTP 500 as `{"detail":"..."}`.

## Route and payload matrix

| Driver operation | Method and exact path | Query/body sent by driver | Wrapper success response | Non-success behavior | Parity |
| --- | --- | --- | --- | --- | --- |
| `pair_room` | `POST /api/rooms/{room_id}/pair` | JSON `{activation_code: string}` | `{room_id, paired: true, connection_state}` | 400 SDK/pair-result; 408 callback timeout; 500/502 setup | Exact |
| `unpair_room` | `POST /api/rooms/{room_id}/unpair` | None | `{room_id, unpaired: true, result, success}` | SDK nonzero is still HTTP 200 with `success:false`; 404/500 otherwise | Transport exact; caller must inspect body |
| `get_room_status` | `GET /api/rooms/{room_id}/status` | None | `{room_id, paired:true, connection_state, get_state_result}` | A failed state read is HTTP 200 with `connection_state:"Unknown"`; 404/500 otherwise | Exact |
| `get_connection_state` | `GET /api/rooms/{room_id}/pre-meeting/connection-state` | None | `{connection_state, connection_state_value}` | 500 on SDK nonzero | Exact |
| `get_meeting_status` | `GET /api/rooms/{room_id}/meeting/status` | None | `{room_id, status, result, success}` | SDK nonzero is HTTP 200 with `success:false` | Transport exact; caller must inspect body |
| `list_rooms` | `GET /api/rooms` | None | `{rooms:[{room_id, paired, connection_state}]}` | Framework 500 on unexpected failure | Exact |
| `start_instant_meeting` | `POST /api/rooms/{room_id}/meeting/start_instant` | None | `{room_id, result, success}` | SDK nonzero is HTTP 200 with `success:false` | Exact; driver validates body |
| `join_meeting` | `POST /api/rooms/{room_id}/meeting/join` | JSON `{meeting_number, password?, bring_share?}` | `{room_id, meeting_number, result, success}` | SDK nonzero is HTTP 200 with `success:false` | Join is exact; supplied password is retained by the caller for the callback flow below |
| `join_meeting_by_url` | `POST /api/rooms/{room_id}/meeting/join-url` | Query `url` | `{room_id, url, result, success}` | SDK nonzero is HTTP 200 with `success:false` | Exact; no obsolete `bring_share` query |
| password callback response | `POST /api/rooms/{room_id}/meeting/password/send` | Query `password:string` | `{room_id, result, success}` | SDK nonzero is HTTP 200 with `success:false`; 404/500 otherwise | Existing callback-response route; caller invokes only after the WebSocket event |
| `start_meeting` | `POST /api/rooms/{room_id}/meeting/start` | JSON `{meeting_number, meeting_name?, host_name?, start_time?, end_time?, bring_share?}` | `{room_id, meeting_number, result, success}` | SDK nonzero is HTTP 200 with `success:false` | Exact; driver validates body |
| `list_meetings` | `GET /api/rooms/{room_id}/meetings/list` | Driver omits optional query `timeout` (default 15 s) | `{room_id, request_result, request_success, list_result, list_success, meetings}` | 408 callback timeout; 500 setup/request failure; callback failure can be HTTP 200 with `list_success:false` | Transport exact; caller must inspect both flags |
| `exit_meeting` | `POST /api/rooms/{room_id}/meeting/exit` | None | `{room_id, result, success}` | SDK nonzero is HTTP 200 with `success:false` | Transport exact; caller must inspect body |
| `confirm_reminder` | `POST /api/rooms/{room_id}/meeting/reminder/confirm-reminder` | JSON `{is_agree, notification_type:int|string}` | `{room_id, result, success}` | Invalid closed-enum value 422; SDK nonzero stays HTTP 200 with `success:false` | Exact; enum names and integers accepted |
| `confirm_custom_reminder` | `POST /api/rooms/{room_id}/meeting/reminder/confirm-custom-reminder` | JSON `{is_agree, notification_type:int|string}` | `{room_id, result, success}` | Nonnumeric unknown name 422; SDK nonzero stays HTTP 200 with `success:false` | Exact after open-int fix; known enum names retained |
| `confirm_consent` | `POST /api/rooms/{room_id}/meeting/reminder/confirm-consent` | JSON `{is_agree, consent_type:int|string, consent_id}` | `{room_id, result, success}` | Invalid closed-enum value 422; SDK nonzero stays HTTP 200 with `success:false` | Exact |
| `confirm_combined_consent` | `POST /api/rooms/{room_id}/meeting/reminder/confirm-combined-consent` | JSON `{is_agree, notification_type:int|string}` | `{room_id, result, success}` | Nonnumeric value 422; SDK nonzero stays HTTP 200 with `success:false` | Exact; open `int64` echo |
| `handle_privacy_alert` | `POST /api/rooms/{room_id}/meeting/reminder/handle-privacy` | JSON `{privacy_alert_action:int|string, privacy_alert_type:int|string}` | `{room_id, result, success}` | Invalid enum 422; SDK nonzero stays HTTP 200 with `success:false` | Exact |
| `continue_on_inactivity` | `POST /api/rooms/{room_id}/meeting/reminder/continue-on-inactivity` | None | `{room_id, result, success}` | SDK nonzero stays HTTP 200 with `success:false` | Exact; driver validates body |
| `respond_to_recording_request` | `POST /api/rooms/{room_id}/recording/respond-to-request` | JSON `{agree, is_persist}` | `{message, agreed, persist}` | SDK nonzero HTTP 500 string detail | Exact |
| `check_recording_disclaimer` | `GET /api/rooms/{room_id}/recording/disclaimer-needed` | None | `{disclaimer_needed}` | SDK nonzero HTTP 500 string detail | Exact |
| `prompt_recording_disclaimer` | `POST /api/rooms/{room_id}/recording/prompt-disclaimer` | None | `{message}` | SDK nonzero HTTP 500 string detail | Exact |
| `ai_companion_on` | `POST /api/rooms/{room_id}/ai-companion/turn-on` | Query `features:int` | `{room_id, features, result, success}` | SDK nonzero is HTTP 200 with `success:false` | Exact; driver validates body |
| `ai_companion_off` | `POST /api/rooms/{room_id}/ai-companion/turn-off` | Query `features:int`, `delete_assets:bool` | `{room_id, features, delete_assets, result, success}` | SDK nonzero is HTTP 200 with `success:false` | Exact; driver validates body |
| AI request: turn on | `POST /api/rooms/{room_id}/ai-companion/respond-to-turn-on` | Query `agree:bool` | `{room_id, agree, result:0, success:true}` | SDK nonzero HTTP 502 with `{detail:{message,error_code,error_name}}` | Exact after structured-error fix |
| AI request: turn off | `POST /api/rooms/{room_id}/ai-companion/respond-to-turn-off` | Query `agree:bool`, `delete_assets:bool` | `{room_id, agree, delete_assets, result:0, success:true}` | SDK nonzero HTTP 502 with `{detail:{message,error_code,error_name}}` | Exact after structured-error fix |
| `confirm_ai_companion_status` | `POST /api/rooms/{room_id}/ai-companion/confirm-status-when-join` | Query `agree:bool` | `{room_id, agree, result:0, success:true}` | SDK nonzero HTTP 502 with `{detail:{message,error_code,error_name}}` | Exact after structured-error fix |
| `cancel_waiting_for_host` | `POST /api/rooms/{room_id}/meeting/cancel-waiting-host` | None | `{room_id, result, success}` | SDK nonzero is HTTP 200 with `success:false` | Exact; driver validates body |
| `mute_audio(true)` | `POST /api/rooms/{room_id}/audio/mute` | None | `{room_id, muted:true, result, success}` | SDK nonzero HTTP 200 with `success:false`; legacy state queries 422 | Exact; driver validates body |
| `mute_audio(false)` | `POST /api/rooms/{room_id}/audio/unmute` | None | `{room_id, muted:false, result, success}` | SDK nonzero HTTP 200 with `success:false`; legacy state queries 422 | Exact; driver validates body |
| `mute_video(true)` | `POST /api/rooms/{room_id}/video/mute` | None | `{room_id, muted:true, result, success}` | SDK nonzero HTTP 200 with `success:false`; legacy state queries 422 | Exact; driver validates body |
| `mute_video(false)` | `POST /api/rooms/{room_id}/video/unmute` | None | `{room_id, muted:false, result, success}` | SDK nonzero HTTP 200 with `success:false`; legacy state queries 422 | Exact; driver validates body |
| `set_speaker_volume` | `POST /api/rooms/{room_id}/settings/volume/speaker` | JSON `{volume:number}` | `{message}` | SDK nonzero HTTP 500 string detail | Exact |
| speaker verification | `GET /api/rooms/{room_id}/settings/volume/speaker` | None | `{volume:number}` | SDK nonzero HTTP 500 string detail | Exact |
| `set_microphone_volume` | `POST /api/rooms/{room_id}/settings/volume/microphone` | JSON `{volume:number}` | `{message}` | SDK nonzero HTTP 500 string detail | Exact |
| microphone verification | `GET /api/rooms/{room_id}/settings/volume/microphone` | None | `{volume:number}` | SDK nonzero HTTP 500 string detail | Exact |
| `start_recording` | `POST /api/rooms/{room_id}/recording/cloud/start` | None | `{message:"Cloud recording started"}` | 409 structured disclaimer/storage precondition; SDK failure 500 `{detail:{message,error_code,error_name,precheck}}` | Exact |
| `set_recording_notification_email` | `POST /api/rooms/{room_id}/recording/notification-email` | JSON `{email:string}` | `{message}` | SDK nonzero HTTP 500 string detail | Exact |
| `stop_recording` | `POST /api/rooms/{room_id}/recording/cloud/stop` | None | `{message:"Cloud recording stopped"}` | SDK failure stays HTTP 500 but is structured `{detail:{message,error_code,error_name}}` | Exact after structured-error fix |
| `pause_recording` | `POST /api/rooms/{room_id}/recording/cloud/pause` | None | `{message:"Cloud recording paused"}` | SDK nonzero HTTP 500 string detail | Exact |
| `resume_recording` | `POST /api/rooms/{room_id}/recording/cloud/resume` | None | `{message:"Cloud recording resumed"}` | SDK nonzero HTTP 500 string detail | Exact |
| `get_participants` | `GET /api/rooms/{room_id}/participants/` | Driver omits optional query `session` (`CurrentSession`) | `{room_id, session, result, success, participants, count}` | SDK nonzero is HTTP 200 with `success:false` | Transport exact; caller must inspect body |
| `wake_up` | `POST /api/rooms/{room_id}/pre-meeting/wake-up` | None | `{message}` | SDK nonzero HTTP 500 string detail | Exact |
| `get_health` | `GET /health` | None | HTTP 200 `{status:"healthy", sdk_initialized, active_rooms, sdk_call_timing}` | HTTP 503 same body plus `reason` when SDK/heartbeat is unhealthy | Exact |

## Event transport

The driver opens `WS /api/rooms/{room_id}/events`. The wrapper accepts the
connection even before pairing, sends SDK event dictionaries from the matching
room queue, and sends `{"event":"keepalive"}` after 30 seconds of inactivity.
There is no inbound command schema. Authentication is expected to be enforced
by deployment ingress; the FastAPI WebSocket route itself does not validate the
driver's optional Basic Authorization header.

Password-protected joins use this event/response handshake:

```json
{
  "event": "OnMeetingNeedsPasswordNotification",
  "showPasswordDialog": true,
  "wrongAndRetry": false,
  "lockStatus": {
    "isLocked": false,
    "remainTimeSec": 0,
    "wrongPwdInputCount": 0
  }
}
```

Only after that event should the caller submit the retained password to
`POST /api/rooms/{room_id}/meeting/password/send?password=...`. The wrapper
does not auto-submit or store credentials.

## Semantic follow-ups outside wrapper route parity

- `IMeetingService::JoinMeetingWithMeetingNumber` has no password argument.
  Password entry therefore uses the SDK's later
  `OnMeetingNeedsPasswordNotification`/`SendMeetingPassword` handshake.
- The wrapper consistently represents many synchronous SDK command failures as
  HTTP 200 with `success:false`. Driver methods using their command-response
  parser handle that. Direct status/list/participant/unpair calls must also
  inspect the documented body flags.
