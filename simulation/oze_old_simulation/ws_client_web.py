# ws_client.py
import asyncio
import websockets
import json
import threading
import time

class WebSocketGameClient:
    def __init__(self, uri):
        self.uri = uri
        self.loop = None
        self.thread = None
        self.running = False
        self.command_queue = asyncio.Queue(maxsize=100)

    async def _connect_and_send_loop(self):
        while self.running:
            connection = None 
            try:
                print(f"Attempting to connect to {self.uri}...")
                connection = await asyncio.wait_for(websockets.connect(self.uri), timeout=5.0)
                print(f"Successfully connected to WebSocket: {self.uri}")
                
                while self.running: 
                    try:
                        command_payload = await asyncio.wait_for(self.command_queue.get(), timeout=0.1)
                        
                        # --- DEBUG PRINT 5 ---
                        if command_payload: 
                            print(f"DEBUG WS_CLIENT: Got from queue: {command_payload}")
                        elif command_payload is None and not self.running:
                            print("DEBUG WS_CLIENT: Got None shutdown signal from queue.")

                        if command_payload is None and not self.running: 
                            self.command_queue.task_done()
                            if not self.running:
                                return 
                            else: 
                                break 
                        
                        if command_payload:
                            # --- DEBUG PRINT 6 ---
                            print(f"DEBUG WS_CLIENT: Attempting to send to WS: {json.dumps(command_payload)}")
                            await connection.send(json.dumps(command_payload))
                            # --- DEBUG PRINT 7 ---
                            print(f"DEBUG WS_CLIENT: Successfully sent to WS: {json.dumps(command_payload)}")
                            self.command_queue.task_done()

                    except asyncio.TimeoutError:
                        continue 
                    except websockets.exceptions.ConnectionClosedOK:
                        print("DEBUG WS_CLIENT: WebSocket connection closed normally (OK).") # Added debug prefix
                        connection = None
                        break 
                    except websockets.exceptions.ConnectionClosedError as e:
                        print(f"DEBUG WS_CLIENT: WebSocket connection closed with error: {e}. Attempting reconnect.") # Added debug prefix
                        connection = None
                        break 
                    except Exception as e_inner:
                        print(f"DEBUG WS_CLIENT: Error in WebSocket send_loop (inner): {e_inner}") # Added debug prefix
                        await asyncio.sleep(0.1) 
                
                if not self.running: break 

            except asyncio.TimeoutError:
                print(f"WebSocket connection to {self.uri} timed out during connect. Retrying...")
            except (websockets.exceptions.InvalidURI, websockets.exceptions.InvalidHandshake, ConnectionRefusedError, OSError) as e_conn_protocol:
                print(f"WebSocket connection/protocol error (outer): {e_conn_protocol}. Retrying...")
            except Exception as e_outer:
                print(f"Unexpected WebSocket error in _connect_and_send_loop (outer): {e_outer}. Retrying...")
            finally:
                if connection:
                    try:
                        print("Ensuring WebSocket connection is closed from outer finally...")
                        await connection.close()
                    except Exception as e_close:
                        print(f"Error explicitly closing websocket in outer finally: {e_close}")
                connection = None 
            
            if not self.running:
                break 
            
            if connection is None and self.running: # Only sleep if retry is needed and client is running
                print("Waiting 5 seconds before retrying connection...")
                await asyncio.sleep(5)

    def _run_event_loop(self):
        self.loop = asyncio.new_event_loop()
        asyncio.set_event_loop(self.loop)
        self.running = True
        try:
            self.loop.run_until_complete(self._connect_and_send_loop())
        except Exception as e:
            print(f"Error running WebSocket event loop: {e}") 
        finally:
            print("Cleaning up command queue...")
            while not self.command_queue.empty():
                try:
                    self.command_queue.get_nowait() 
                    self.command_queue.task_done()
                except asyncio.QueueEmpty:
                    break
                except Exception as e_q_final: 
                    print(f"Exception during final queue cleanup: {e_q_final}")

            if self.loop and self.loop.is_running():
                print("Stopping asyncio event loop...")
                self.loop.call_soon_threadsafe(self.loop.stop)
            
            if self.loop and not self.loop.is_closed():
                # Wait for the loop to actually stop before closing
                # This can be tricky; ensuring all tasks are cancelled/completed is key
                # For simplicity here, we'll rely on loop.stop() and then close.
                # A more robust shutdown might involve cancelling pending tasks.
                pass # Loop will be closed by the thread finishing or explicit stop.

            # Moving loop.close() to be absolutely sure it's called if loop exists.
            # However, it should ideally be closed after it has fully stopped.
            # If the loop is still running when close() is called from another thread,
            # it can lead to issues. Let's ensure it's stopped.
            if self.loop: # Check if loop object exists
                if self.loop.is_running():
                    # If it's still running, try to stop it again or wait a moment
                    self.loop.call_soon_threadsafe(self.loop.stop)
                    # Give it a moment to process the stop if called from here
                    # This part is tricky and depends on how the loop exits run_until_complete
                    # For now, we assume run_until_complete finishes before this finally block's end.
                
                # Only close if it's not already closed.
                if not self.loop.is_closed():
                    self.loop.close()
                    print("Asyncio event loop closed in _run_event_loop finally.")
            
            print("WebSocket event loop fully stopped and resources handled.")


    def start(self):
        if not self.thread or not self.thread.is_alive():
            self.thread = threading.Thread(target=self._run_event_loop, daemon=True)
            self.thread.start()
            print("WebSocket client thread started.")

    def stop(self):
        print("Attempting to stop WebSocket client...")
        self.running = False 

        if self.loop and self.loop.is_running():
            try:
                future = asyncio.run_coroutine_threadsafe(self.command_queue.put(None), self.loop)
                try:
                    future.result(timeout=1.0) 
                except TimeoutError:
                    print("Timeout putting shutdown signal on queue.")
                except Exception as e_put_exc:
                    print(f"Exception putting shutdown signal: {e_put_exc}")
            except Exception as e_outer_put: 
                print(f"Error during shutdown signal queuing: {e_outer_put}")
        
        if self.thread and self.thread.is_alive():
            print(f"Joining WebSocket client thread (timeout 7s)...")
            self.thread.join(timeout=7) 
            if self.thread.is_alive():
                print("Warning: WebSocket client thread did not stop gracefully within timeout.")
            else:
                print("WebSocket client thread joined.")
        
        # Clean up loop reference after thread join
        if self.loop and not self.loop.is_closed():
            # If the loop wasn't closed by _run_event_loop's finally (e.g. thread killed)
            # This is a last-ditch effort, but ideally _run_event_loop handles its own loop closing.
            print("Warning: Event loop may not have closed cleanly from its own thread. Attempting close from stop().")
            try:
                # This can be problematic if called from a different thread than the one running the loop
                # self.loop.close() 
                pass # Better to let _run_event_loop handle its own loop's closure
            except Exception as e_loop_close_stop:
                print(f"Error closing loop in stop(): {e_loop_close_stop}")

        self.loop = None 
        print("WebSocket client resources released.")

    # --- THIS IS THE MISSING METHOD ---
    def send_joystick_command(self, userid: int, x: float, y: float):
        if not self.running:
            # print("DEBUG WS_CLIENT: Client not running, command not sent.") # Optional: can be spammy
            return

        joystick_str = f"x: {x:.2f}, y: {y:.2f}"
        payload = {
            "type": "joystick",
            "userid": userid,
            "joystick": joystick_str
        }
        try:
            # --- DEBUG PRINT 4 ---
            print(f"DEBUG WS_CLIENT: Adding to queue: {payload}")
            self.command_queue.put_nowait(payload)
        except asyncio.QueueFull:
            print("DEBUG WS_CLIENT: WebSocket command queue is full. Command for B1 dropped.")
    # --- END OF MISSING METHOD ---


# Global instance for the WebSocket client
WS_CLIENT_URI = "ws://192.168.48.40:8000/ws/mobilecontrol"
ws_game_client = None # This will be initialized by init_global_ws_client

def init_global_ws_client():
    global ws_game_client
    if ws_game_client is None:
        print(f"Initializing WebSocket client for URI: {WS_CLIENT_URI}")
        ws_game_client = WebSocketGameClient(WS_CLIENT_URI)
        ws_game_client.start()
    else:
        print("WebSocket client already initialized.")


def shutdown_global_ws_client():
    global ws_game_client
    if ws_game_client:
        print("Shutting down WebSocket client...")
        ws_game_client.stop()
        ws_game_client = None
        print("Global WebSocket client instance cleared.")
    else:
        print("No active WebSocket client to shut down.")