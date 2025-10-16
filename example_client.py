#!/usr/bin/env python3
"""
Example client demonstrating how to interact with the Zoom Rooms SDK microservice
"""

import asyncio
import aiohttp
import json


class ZoomRoomsClient:
    """Client for the Zoom Rooms SDK microservice"""

    def __init__(self, base_url: str = "http://localhost:8000"):
        self.base_url = base_url

    async def pair_room(self, room_id: str, activation_code: str):
        """Pair a Zoom Room"""
        async with aiohttp.ClientSession() as session:
            async with session.post(
                f"{self.base_url}/api/rooms/{room_id}/pair",
                json={"activation_code": activation_code}
            ) as resp:
                return await resp.json()

    async def start_instant_meeting(self, room_id: str):
        """Start an instant meeting"""
        async with aiohttp.ClientSession() as session:
            async with session.post(
                f"{self.base_url}/api/rooms/{room_id}/meeting/start_instant"
            ) as resp:
                return await resp.json()

    async def join_meeting(self, room_id: str, meeting_number: str, password: str = ""):
        """Join a meeting by number"""
        async with aiohttp.ClientSession() as session:
            async with session.post(
                f"{self.base_url}/api/rooms/{room_id}/meeting/join",
                json={"meeting_number": meeting_number, "password": password}
            ) as resp:
                return await resp.json()

    async def exit_meeting(self, room_id: str):
        """Exit the current meeting"""
        async with aiohttp.ClientSession() as session:
            async with session.post(
                f"{self.base_url}/api/rooms/{room_id}/meeting/exit"
            ) as resp:
                return await resp.json()

    async def mute_audio(self, room_id: str, mute: bool = True):
        """Mute/unmute audio"""
        async with aiohttp.ClientSession() as session:
            async with session.post(
                f"{self.base_url}/api/rooms/{room_id}/audio/mute?mute={str(mute).lower()}"
            ) as resp:
                return await resp.json()

    async def mute_video(self, room_id: str, mute: bool = True):
        """Mute/unmute video"""
        async with aiohttp.ClientSession() as session:
            async with session.post(
                f"{self.base_url}/api/rooms/{room_id}/video/mute?mute={str(mute).lower()}"
            ) as resp:
                return await resp.json()

    async def listen_to_events(self, room_id: str, callback):
        """Listen to real-time events via WebSocket"""
        ws_url = f"ws://localhost:8000/api/rooms/{room_id}/events"

        async with aiohttp.ClientSession() as session:
            async with session.ws_connect(ws_url) as ws:
                print(f"Connected to events for room: {room_id}")

                async for msg in ws:
                    if msg.type == aiohttp.WSMsgType.TEXT:
                        event = json.loads(msg.data)
                        await callback(event)
                    elif msg.type == aiohttp.WSMsgType.ERROR:
                        print(f"WebSocket error: {ws.exception()}")
                        break


async def example_event_handler(event: dict):
    """Example callback for handling events"""
    event_type = event.get("event")

    if event_type == "OnPairRoomResult":
        result = event.get("result")
        if result == 0:
            print("✓ Room paired successfully!")
        else:
            print(f"✗ Room pairing failed: {result}")

    elif event_type == "OnUpdateMeetingStatus":
        status = event.get("status")
        print(f"Meeting status changed: {status}")

    elif event_type == "OnZRConnectionStateChanged":
        state = event.get("state")
        print(f"Connection state changed: {state}")

    elif event_type == "OnConfReadyNotification":
        print("✓ Conference is ready!")

    elif event_type == "OnExitMeetingNotification":
        print("Meeting exited")

    else:
        print(f"Event: {event}")


async def example_usage():
    """Example demonstrating typical usage patterns"""

    client = ZoomRoomsClient()
    room_id = "conference_room_1"

    print("=" * 60)
    print("Zoom Rooms SDK Microservice - Example Client")
    print("=" * 60)

    # Start listening to events in the background
    event_task = asyncio.create_task(
        client.listen_to_events(room_id, example_event_handler)
    )

    # Give the WebSocket connection time to establish
    await asyncio.sleep(1)

    try:
        # Example 1: Pair a room (replace with your actual activation code)
        print("\n[1] Pairing room...")
        print("NOTE: Replace 'YOUR-ACTIVATION-CODE' with actual code")
        # result = await client.pair_room(room_id, "123-456-789")
        # print(f"Pair result: {result}")

        # Wait for pairing to complete
        await asyncio.sleep(2)

        # Example 2: Start an instant meeting
        print("\n[2] Starting instant meeting...")
        result = await client.start_instant_meeting(room_id)
        print(f"Start meeting result: {result}")

        # Wait for meeting to connect
        await asyncio.sleep(5)

        # Example 3: Mute/unmute audio
        print("\n[3] Muting audio...")
        result = await client.mute_audio(room_id, mute=True)
        print(f"Mute result: {result}")

        await asyncio.sleep(2)

        print("\n[4] Unmuting audio...")
        result = await client.mute_audio(room_id, mute=False)
        print(f"Unmute result: {result}")

        # Example 4: Mute video
        print("\n[5] Muting video...")
        result = await client.mute_video(room_id, mute=True)
        print(f"Mute video result: {result}")

        # Wait a bit
        await asyncio.sleep(5)

        # Example 5: Exit meeting
        print("\n[6] Exiting meeting...")
        result = await client.exit_meeting(room_id)
        print(f"Exit result: {result}")

        # Keep listening to events for a bit longer
        print("\n[7] Listening to events for 5 more seconds...")
        await asyncio.sleep(5)

    except KeyboardInterrupt:
        print("\nInterrupted by user")

    except Exception as e:
        print(f"\nError: {e}")

    finally:
        # Cancel event listening
        event_task.cancel()
        try:
            await event_task
        except asyncio.CancelledError:
            pass

    print("\n" + "=" * 60)
    print("Example complete!")
    print("=" * 60)


async def simple_example():
    """Simpler example showing just the REST API"""

    client = ZoomRoomsClient()
    room_id = "test_room"

    # Check service is running
    async with aiohttp.ClientSession() as session:
        async with session.get("http://localhost:8000/") as resp:
            print(await resp.json())

    # Start a meeting
    result = await client.start_instant_meeting(room_id)
    print(f"Started meeting: {result}")

    # Mute audio
    result = await client.mute_audio(room_id, True)
    print(f"Muted audio: {result}")


if __name__ == "__main__":
    # Choose which example to run
    print("Choose an example:")
    print("1. Full example with events (recommended)")
    print("2. Simple REST-only example")
    choice = input("Enter 1 or 2 [1]: ").strip() or "1"

    if choice == "2":
        asyncio.run(simple_example())
    else:
        asyncio.run(example_usage())
