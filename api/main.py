# main.py

import asyncio
from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
import re
import json

app = FastAPI()

connectedUsers = 0
maxConnectedUsers = 2

gameState = {
    "connectedUsers": connectedUsers,
    "maxConnectedUsers": maxConnectedUsers,
    "connections": [],
    "difficulty": ""
}


@app.get("/")
def read_root():
    return {"Hello": "World"}


@app.websocket("/ws/tv/onloading")
async def websocket_tv_onloading(websocket: WebSocket):
    await websocket.accept()
    previous_connected_users = None
    try:
        while True:
            if gameState["connectedUsers"] != previous_connected_users:
                await websocket.send_text(str(gameState["connectedUsers"]))
                previous_connected_users = gameState["connectedUsers"]
            await asyncio.sleep(1)  # Adjust the interval as needed
    except Exception as e:
        print(f"Error: {e}")
    finally:
        await websocket.close()


@app.websocket("/ws/mobile")
async def websocket_mobile(websocket: WebSocket):
    if gameState["connectedUsers"] >= gameState["maxConnectedUsers"]:
        await websocket.close()
        return
    else:
        gameState["connectedUsers"] += 1
        user_id = gameState["connectedUsers"]
        await websocket.accept()

        async def broadcast():
            for connection in gameState["connections"]:
                await connection.send_json({'userid': user_id, 'connectedUsers': gameState["connectedUsers"], 'difficulty': gameState["difficulty"]})

        gameState["connections"].append(websocket)
        await broadcast()

        try:
            while True:
                data = await websocket.receive_json()
                if data.get("type") == "difficulty":
                    gameState["difficulty"] = data["difficulty"]
                await broadcast()
        except Exception as e:
            print(f"Error: {e}")
        finally:
            gameState["connectedUsers"] -= 1
            gameState["connections"].remove(websocket)
            await broadcast()


connected_robots = []
connected_users = []


@app.get("/debug")
def debug():
    print("connected-robots:" + str(connected_robots))
    print("connected-users:" + str(connected_users))

    return "check da log !"


@app.websocket("/ws/robotcontrol")
async def robot_control(websocket: WebSocket):
    await websocket.accept()

    # go through the connected_robots list. they are numbered with robot_number
    # find the smallest number and assign it to the new robot
    # if all numbers 1-4 are taken, reject the connection

    solved = False
    for i in range(1, 5):
        if (i not in [robot["robot_number"] for robot in connected_robots]):
            solved = True
            robot_number = i
            break

    connected_robots.append({
        "websocket": websocket,
        "robot_number": robot_number
    })
    print("ESP32 connected, allocated robot number" + str(len(connected_robots)))

    try:
        while True:
            data = await websocket.receive_text()
            print(f"Received from ESP32: {data}")

    except WebSocketDisconnect:
        # Remove the robot dict associated with this websocket
        for robot in connected_robots:
            if robot["websocket"] == websocket:
                connected_robots.remove(robot)
                break
        print("ESP32 disconnected")


@app.websocket("/ws/mobilecontrol")
async def mobile_control(websocket: WebSocket):
    await websocket.accept()
    print("Mobile connected")

    try:
        while True:
            data = await websocket.receive_text()
            print(f"Received from mobile: {data}")
            print(f"Current connected robots: {connected_robots}")
            print(f"Current connected users: {connected_users}")

            try:
                msg = json.loads(data)
                if msg.get("type") == "buttons" and "buttons" in msg:
                    # Extract x and y from string like "x: -0.91, y: 0.09"
                    if (msg.get("buttons") == "ACW"):
                        message = {'x': -99, 'y': -99}
                    elif (msg.get("buttons") == "CW"):
                        message = {'x': 99, 'y': 99}

                    for robot in connected_robots:
                        if (robot["robot_number"] == msg.get("userid")):
                            try:
                                print(
                                    f"Sending command to robot {robot['robot_number']}: {msg.get('buttons')} from user {msg['userid']}")
                                await robot["websocket"].send_text(json.dumps(message))
                            except:
                                connected_robots.remove(
                                    robot)

                if msg.get("type") == "joystick" and "joystick" in msg:
                    # Extract x and y from string like "x: -0.91, y: 0.09"
                    for robot in connected_robots:
                        if (robot["robot_number"] == msg.get("userid")):

                            try:
                                print(
                                    f"Sending command to robot {robot['robot_number']}: {msg.get('joystick')} from user {msg['userid']}")
                                await robot["websocket"].send_text(json.dumps(msg.get("joystick")))
                            except:
                                connected_robots.remove(
                                    robot)
            except Exception as e:
                print(f"Error parsing joystick data: {e}")

            # Optionally, parse and respond to mobile status
            # await websocket.send_text("Command received")  # Acknowledge
    except WebSocketDisconnect:

        # Remove the mobile dict associated with this websocket

        for user in connected_users:
            if user["websocket"] == websocket:
                connected_users.remove(user)
                break

        print("Mobile disconnected")


@app.post("/send_command/{cmd}")
async def send_command(cmd: str):
    for robot_ws in list(connected_robots):
        try:
            await robot_ws.send_text(cmd)
        except:
            connected_robots.discard(robot_ws)
    return {"status": "sent", "command": cmd}
