 // Определяем адрес WebSocket-сервера
 const socket = new WebSocket(`ws://${window.location.host}/ws/moscow_module/`);

 // Обработчик открытия соединения
 socket.onopen = function () {
     console.log("WebSocket подключен");
     socket.send(JSON.stringify({type: 'ping'}));
 };

 // Обработчик ошибок
 socket.onerror = function (error) {
     console.error("Ошибка WebSocket:", error);
 };

 // Обработчик получения сообщения
 socket.onmessage = function (event) {
     const data = JSON.parse(event.data);
     console.log("Получены данные:", data);

     // Обновляем содержимое на странице
     const container = document.getElementById("data-container");
     if (data.type === "update") {
         container.innerHTML = `<pre>${JSON.stringify(data.message, null, 2)}</pre>`;
     }
 };

 // Обработчик закрытия соединения
 socket.onclose = function (event) {
     console.log("WebSocket закрыт:", event);
 };