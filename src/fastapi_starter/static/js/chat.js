// Connects to the echo WebSocket on whatever host/port served this page.
const scheme = location.protocol === "https:" ? "wss" : "ws";
const ws = new WebSocket(`${scheme}://${location.host}/ws/echo`);
const list = document.getElementById("messages");
const input = document.getElementById("message");

ws.addEventListener("message", (event) => {
  const item = document.createElement("li");
  item.textContent = event.data;
  list.appendChild(item);
});

document.getElementById("chat").addEventListener("submit", (event) => {
  event.preventDefault();
  if (input.value && ws.readyState === WebSocket.OPEN) {
    ws.send(input.value);
    input.value = "";
  }
});
