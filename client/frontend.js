// frontend.js

const ws = new WebSocket("ws://localhost:8000/ws");

ws.onmessage = (event) => {
    const gameState = JSON.parse(event.data);
    if (gameState.user_input_needed) {
        // Prompt the user for input
        document.getElementById("input-prompt").innerText = gameState.current_scene;
        document.getElementById("input-field").style.display = "block";
    } else {
        document.getElementById("input-field").style.display = "none";
    }
};

async function sendInput() {
    const input = document.getElementById("user-input").value;
    await fetch("/input", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ input })
    });
    document.getElementById("user-input").value = "";
}
