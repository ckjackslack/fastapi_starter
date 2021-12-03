let ws = new WebSocket('ws://localhost:8099/pizza/ws')
let msg_list = document.getElementById('messages')

ws.onmessage = function(event) {
    let message = document.createElement('li')
    let content = document.createTextNode(event.data)
    message.appendChild(content)
    msg_list.appendChild(message)
}

function sendMessage(event) {
    let input = document.getElementById('messageText')
    ws.send(input.value)
    input.value = ''
    event.preventDefault()
}