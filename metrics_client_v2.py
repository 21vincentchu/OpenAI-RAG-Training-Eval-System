"""
VR Metrics Client v2 - WebSocket Client for Struggle Event Monitoring

This script connects to a VR server via WebSocket to subscribe to and monitor
"struggle events" from VR devices. It receives real-time data about user interactions,
including gaze tracking metrics, and saves all events to a JSON Lines file for analysis.

Main functionality:
- Connects to a WebSocket server hosting VR device data
- Subscribes to specific devices (or all devices with "*")
- Receives struggle events with associated gaze tracking data
- Logs events to console and saves them to a .jsonl file
"""

import asyncio
import json
import argparse
import websockets
from chroma_vector_store import answer_question_json


def summarize_gaze(gaze: dict) -> str:
    """
    Create a human-readable summary of gaze tracking data.

    Gaze data includes information about where a user was looking and for how long.
    This function extracts key metrics to display a compact summary.

    Args:
        gaze: Dictionary containing gaze tracking information with structure:
              {
                  "summary": {
                      "top_labels": [(label, duration_sec), ...],  # Most looked-at items
                      "entropy_bits": float,                        # Measure of gaze dispersion
                      "total_dwell_sec": float                      # Total time spent gazing
                  }
              }

    Returns:
        A formatted string summarizing the gaze metrics, e.g.:
        "entropy≈2.45, total_dwell≈15.3s, top=[button:5.2s, menu:3.1s, icon:2.0s]"

        - entropy: Higher values mean gaze is more scattered across many items
        - total_dwell: Total time the user's gaze was tracked
        - top: The 3 items the user looked at most, with durations
    """
    if not gaze:
        return "(no gaze)"
    summ = gaze.get("summary", {}) or {}
    top = summ.get("top_labels") or []
    # Format the top 3 most-viewed items with their dwell times
    top_str = ", ".join(f"{lbl}:{sec:.1f}s" for lbl, sec in top[:3])
    e = summ.get("entropy_bits", 0.0)
    td = summ.get("total_dwell_sec", 0.0)
    return f"entropy≈{e:.2f}, total_dwell≈{td:.1f}s, top=[{top_str}]"

async def run(
    uri: str,
    devices: list[str] | None,
    gaze_window_sec: float,
    max_events: int,
    save_json: bool = True,  # Enabled by default
    out_path: str = "metrics_client_dump.jsonl",
):
    """
    Main async function that connects to the VR server and processes struggle events.

    This function:
    1. Opens a WebSocket connection to the server
    2. Sends a "client_hello" message to register as a processor client
    3. Waits for acknowledgment messages from the server
    4. Continuously receives and processes struggle events
    5. Saves all messages to a JSON Lines (.jsonl) file

    Args:
        uri: WebSocket server URI (e.g., "ws://127.0.0.1:8765")
        devices: List of device IDs to subscribe to, or None to subscribe to all devices
        gaze_window_sec: Time window in seconds for aggregating gaze data (e.g., 20.0 means
                         gaze data is aggregated over the last 20 seconds before an event)
        max_events: Maximum number of gaze events to include in analysis
        save_json: If True, saves all received messages to a .jsonl file
        out_path: File path for saving the JSON Lines output

    The function runs indefinitely until the connection closes or KeyboardInterrupt.
    """
    # Open output file for appending if JSON saving is enabled
    dump_f = open(out_path, "a", encoding="utf-8") if save_json else None
    try:
        # Connect to WebSocket server with 8MB max message size
        async with websockets.connect(uri, max_size=8*1024*1024) as ws:
            # Build the initial handshake message to register with the server
            hello = {
                "type": "client_hello",
                "role": "processor",  # This client will process struggle events
                "subscribe": "*" if not devices else devices,  # "*" = all devices
                "subscribe_opts": {
                    "gaze_window_sec": gaze_window_sec,  # Time window for gaze aggregation
                    "max_events": max_events  # Max gaze events to include
                },
                "product": "MetricsClient",
                "platform": "Python",
            }
            await ws.send(json.dumps(hello))
            print(f"[CLIENT] -> hello: {hello}")

            # Wait for acknowledgment messages from the server
            # The server typically sends hello_ack and subscribe_ack
            for _ in range(2):
                try:
                    # Wait up to 1 second for each ack message
                    raw_ack = await asyncio.wait_for(ws.recv(), timeout=1.0)
                    try:
                        msg_ack = json.loads(raw_ack)
                    except Exception:
                        # If message isn't JSON, just log it
                        print(f"[CLIENT] non-JSON ack: {raw_ack[:200]}")
                        continue
                    print(f"[CLIENT] <- {msg_ack}")
                    # Save acknowledgment to output file
                    if dump_f:
                        dump_f.write(json.dumps(msg_ack, ensure_ascii=False) + "\n")
                        dump_f.flush()
                except Exception:
                    # Timeout or other error - stop waiting for acks
                    break


            # ------------------ INTEGRATE CODE HERE --------------#
            # it should receive a JSON and then call code in chroma vector store which takes in a json, answers the question using the vector store, and then returns it as a json

            # Main message receiving loop - runs continuously until connection closes
            while True:
                try:
                    # Wait for the next message from the server
                    raw = await ws.recv()
                except websockets.ConnectionClosed:
                    print("[CLIENT] connection closed")
                    break

                try:
                    # Parse the JSON message
                    msg = json.loads(raw)
                except Exception:
                    # If it's not valid JSON, log and skip
                    print("[CLIENT] non-JSON message:", raw[:200])
                    continue

                # Save every received message to the output file (if enabled)
                if dump_f:
                    dump_f.write(json.dumps(msg, ensure_ascii=False) + "\n")
                    dump_f.flush()
                    
                '''
                AI Question Handling Integration
                If the incoming message contains a "question" field, it's treated as a query
                for the AI-powered vector store. This allows end devices to ask questions
                about documentation or system information stored in the ChromaDB vector store.
                
                Flow:
                    1. Client/device sends JSON: {"question": "How do I reset my device?"}
                    2. answer_question_json() queries the vector store for relevant context
                    3. OpenAI API generates a concise answer based on the retrieved documents
                    4. Response JSON is sent back: {"timestamp": "...", "answer": "..."}
                '''
        
                if "question" in msg:
                    print(f"[AI] Received question: {msg.get('question')}")
                    # Call chroma vector store to answer the question
                    response = answer_question_json(msg)
                    print(f"[AI] Response: {response}")

                    # Validate JSON before sending
                    try:
                        # Test serialization to ensure valid JSON
                        json_test = json.dumps(response)
                        # Test deserialization to verify structure
                        parsed = json.loads(json_test)
                        print(f"[AI] JSON validation passed. Keys: {list(parsed.keys())}")
                        # Send the response back to the server
                        await ws.send(json_test)
                    except (TypeError, ValueError) as e:
                        print(f"[AI] ERROR: Invalid JSON response: {e}")
                        print(f"[AI] Response type: {type(response)}, value: {response}")
                    continue

                # Process different message types
                t = msg.get("type")
                if t == "struggle_event":
                    # A "struggle event" indicates a user had difficulty with something in VR
                    # Examples: errors, confusion, repeated failed attempts, etc.
                    dev_id = msg.get("device_id")
                    dev_lbl = msg.get("device_label") or dev_id
                    ev = msg.get("event", {})  # Contains: kind, detail, at (timestamp)
                    gaze = msg.get("gaze", {})  # Contains gaze tracking data during the event

                    # Print the struggle event details
                    print(f"[STRUGGLE][{dev_lbl}] {ev.get('kind')}: {ev.get('detail')} @ {ev.get('at')}")
                    # Print the associated gaze summary to understand where user was looking
                    print("  ", summarize_gaze(gaze))
                elif t in ("hello_ack", "subscribe_ack"):
                    # Acknowledgment messages confirming connection/subscription
                    print("[CLIENT]", t, msg)
                elif t == "broadcast_message":
                    # General broadcast messages from the server
                    print("[BROADCAST]", msg.get("payload"))
                else:
                    # Unknown message type - silently ignore
                    pass
    finally:
        # Clean up: close the output file if it was opened
        if dump_f:
            dump_f.close()

if __name__ == "__main__":
    """
    Command-line entry point for the metrics client.

    Example usage:
        # Connect to default server (127.0.0.1:8765) and subscribe to all devices
        python metrics_client_v2.py

        # Subscribe to specific devices
        python metrics_client_v2.py --device device123 --device device456

        # Connect to a different server with custom gaze parameters
        python metrics_client_v2.py --host 192.168.1.100 --port 9000 --gwin 30.0 --gmax 500

        # Disable JSON file output (just print to console)
        python metrics_client_v2.py --no-save-json
    """
    ap = argparse.ArgumentParser(description="Subscribe to struggle events from the VR server.")
    ap.add_argument("--host", default="127.0.0.1", help="WebSocket server host (default: 127.0.0.1)")
    ap.add_argument("--port", type=int, default=8765, help="WebSocket server port (default: 8765)")
    ap.add_argument("--device", action="append", help="Device ID to subscribe to. Can be repeated for multiple devices. Omit to subscribe to all devices.")
    ap.add_argument("--gwin", type=float, default=20.0, help="Gaze window in seconds - how far back to aggregate gaze data (default: 20.0)")
    ap.add_argument("--gmax", type=int, default=200, help="Max gaze events to include in analysis (default: 200)")
    ap.add_argument("--no-save-json", action="store_true", help="Disable saving received messages to .jsonl file (default: saving enabled)")
    ap.add_argument("--out", default="metrics_client_dump.jsonl", help="Output file path for saving JSON messages (default: metrics_client_dump.jsonl)")
    args = ap.parse_args()

    # Build WebSocket URI from host and port
    uri = f"ws://{args.host}:{args.port}"
    try:
        # Run the async client
        asyncio.run(
            run(
                uri,
                args.device,  # None if not specified, meaning subscribe to all
                args.gwin,
                args.gmax,
                save_json=not args.no_save_json,
                out_path=args.out,
            )
        )
    except KeyboardInterrupt:
        # Clean exit on Ctrl+C
        pass
