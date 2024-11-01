# server.py
# -------------------
import asyncio
import yaml
import sys
import logging
import os
# -------------------
from fastapi import FastAPI, WebSocket, HTTPException
from fastapi.responses import HTMLResponse
from fastapi.websockets import WebSocketDisconnect  # Add this import
from fastapi.staticfiles import StaticFiles
# -------------------
from run_game import main as run_game_main
from core.job_manager import enqueue_user_input_job, get_user_input
# -------------------
# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI()

# Ensure the audio directory exists
os.makedirs("static/audio", exist_ok=True)

# Mount the static files route
app.mount("/static", StaticFiles(directory="static"), name="static")

# Load the initial situation from YAML
with open("game_config.yaml", "r") as f:
    config = yaml.safe_load(f)
initial_situation = config["initial_situation"]

# Store WebSocket connections for broadcasting logs
connected_clients = []

@app.on_event("startup")
async def start_game():
    logger.info("!!!Starting game with initial situation: %s", initial_situation)  # Debug info
    print("@@@Starting game with initial situation: ", initial_situation)  
    asyncio.create_task(run_game_main(initial_situation, connected_clients))

@app.get("/")
async def get_console():
    logger.info("Serving console page...")  # Debug info
    return HTMLResponse(html_content)

@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    logger.info("WebSocket connection established.")
    await websocket.accept()
    connected_clients.append(websocket)

    try:
        while True:
            data = await websocket.receive_text()
            logger.info("Received data from client: %s", data)

            if data.startswith("INPUT:"):
                user_input_value = data.split("INPUT:")[1].strip()
                logger.info("User input received: %s", user_input_value)
                print(f"User input received: {user_input_value}")
                await enqueue_user_input_job(user_input_value)

    except WebSocketDisconnect:
        logger.info("WebSocket connection closed.")
    except Exception as e:
        logger.error("WebSocket error: %s", e)
    finally:
        connected_clients.remove(websocket)
        logger.info("WebSocket connection removed.")

# Redirect print statements to WebSocket clients for console output
class WebSocketConsole:
    def write(self, message):
        for client in connected_clients[:]:  # Iterate over a copy of the list
            try:
                asyncio.create_task(client.send_text(message))
            except Exception as e:
                logger.error("Failed to send message to WebSocket client: %s", e)
                connected_clients.remove(client)  # Remove disconnected clients
    def flush(self):
        pass

# Redirect standard output to WebSocketConsole
print("=============1")
logger.info("-------------1")
logger.info("Redirecting stdout to WebSocketConsole.")
sys.stdout = WebSocketConsole()
print("=============2")
logger.info("-------------2")

# HTML content for the console interface
html_content = """
<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8">
  <title>Game Console</title>
  <style>
    #console {
      font-family: monospace;
      background: #222;
      color: #eee;
      padding: 10px;
      max-height: 80vh;
      overflow-y: auto;  /* Scrollable when content overflows */
      height: 60vh;  /* Initial height to view more lines */
      border: 1px solid #444;
      margin-bottom: 10px;
    }
    #input-container {
      display: flex;
      margin-top: 10px;
    }
    #user-input {
      flex: 1;
      padding: 10px;
      font-size: 16px;
      color: #333;
    }
  </style>
</head>
<body>
  <div id="console"></div>
  <div id="input-container">
    <input id="user-input" placeholder="Type your input here..." onkeypress="handleKeyPress(event)">
  </div>

  <script>
    const consoleDiv = document.getElementById("console");
    const userInput = document.getElementById("user-input");
    const ws = new WebSocket("ws://localhost:8000/ws");

    // Display incoming messages
    ws.onmessage = function(event) {
      const message = event.data;
      console.log("Received message from server:", message);  // Debug info
      const messageElement = document.createElement("div");
      messageElement.textContent = message;
      consoleDiv.appendChild(messageElement);

      // Auto-scroll to the bottom
      consoleDiv.scrollTop = consoleDiv.scrollHeight;
    };

    // Confirm connection
    ws.onopen = function() {
      console.log("WebSocket connection established.");  // Debug info
    };

    // WebSocket error handling
    ws.onerror = function(error) {
      console.error("WebSocket error:", error);  // Debug info
    };

    // WebSocket close handling
    ws.onclose = function() {
      console.log("WebSocket connection closed.");  // Debug info
    };

    // Send user input to the server
    function handleKeyPress(event) {
      if (event.key === "Enter") {
        const input = userInput.value;
        console.log("Sending user input to server:", input);  // Debug info
        ws.send("INPUT:" + input);
        userInput.value = "";  // Clear input field
      }
    }

    ws.onmessage = function(event) {
        const message = event.data;

        if (message.startsWith("AUDIO:")) {
            const audioUrl = message.replace("AUDIO:", "").trim();
            console.log("Playing audio from:", audioUrl);  // Debug message
            const audio = new Audio(audioUrl);  // Create a new Audio object
            audio.play();  // Play the audio
        } else {
            // Handle other messages as before
            const messageElement = document.createElement("div");
            messageElement.textContent = message;
            document.getElementById("console").appendChild(messageElement);
            document.getElementById("console").scrollTop = consoleDiv.scrollHeight;
        }
    }; 
  </script>
</body>
</html>
"""

