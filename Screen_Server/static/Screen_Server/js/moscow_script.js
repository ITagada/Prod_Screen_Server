let stops = null;
let socket = null;
let reconnectAttempts = 0;
let serverTime = null;
let localOffset = 0;
const maxReconnectAttempts = 60;
const reconnectInterval = 1000;

function createWebSocket() {
    // Определяем адрес WebSocket-сервера
    socket = new WebSocket(`ws://${window.location.host}/ws/moscow_module/`);

    // Обработчик открытия соединения
    socket.onopen = function () {
        console.log("WebSocket подключен");
        socket.send(JSON.stringify({type: 'ping'}));
        reconnectAttempts = 0;
    };

    // Обработчик ошибок
    socket.onerror = function (error) {
        console.error("Ошибка WebSocket:", error);
    };

    // Обработчик получения сообщения
    socket.onmessage = function (event) {
        const data = JSON.parse(event.data);
        console.log("Получены данные:", data);

        if (data.start_stops) {
            stops = data.start_stops;
            console.log('Стартовая отрисовка');
            renderStops(stops);
            updateProgressBar(data.currentStationIndex, data.nextStationIndex);
        }

        if (data.message && data.message.dataType === 'RouteData') {
            const newStops = data.message.stops;
            if (isStopsChanged(newStops)) {
                stops = newStops;
                console.log('Маршрут изменился, обновляем...');
                renderStops(stops);
            } else {
                console.log('Маршрут не изменился, пропускаем обновление.');
            }
        }

        if (data.message && data.message.dataType === 'OperationalData') {
            console.log("Данные типа:", data.message.dataType);
            updateProgressBar(data.message.currentStationIndex, data.message.nextStationIndex);
            if (data.message?.time) {
                let time = data.message.time;
                handleServerMessage(time);
            }
        }
    };

    // Обработчик закрытия соединения
    socket.onclose = function (event) {
        console.log("WebSocket закрыт:", event);

        if (reconnectAttempts < maxReconnectAttempts) {
            setTimeout(() => {
                console.log(`Попытка переподключения: ${reconnectAttempts + 1}`);
                reconnectAttempts++;
                createWebSocket();
            }, reconnectInterval);
        } else {
            console.error('Максимальное количество попыток переподключения достигнуто');
        }
    };
}

createWebSocket();

function isStopsChanged(newStops) {
    if (!stops || stops.length !== newStops.length) {
        return true;
    }
    return stops.some((stop, index) => {
        return stop.stationID !== newStops[index].stationID;
    });
}

function renderStops(stops) {
    const routeElement = document.getElementById('route');

    // Очищаем старые точки перед отрисовкой новых
    document.querySelectorAll('.stop, .label-wrapper').forEach(el => el.remove());

    stops.forEach(stop => {
        const stopElement = document.createElement('div');
        stopElement.className = 'stop';
        stopElement.style.left = stop.position + '%';

        const labelWrapper = document.createElement('div');
        labelWrapper.className = 'label-wrapper';
        labelWrapper.style.left = stop.position + '%';

        const label = document.createElement('div');
        label.className = 'label';
        label.innerText = stop.stationName;

        labelWrapper.appendChild(label);
        routeElement.appendChild(stopElement);
        routeElement.appendChild(labelWrapper);
    });
}

function updateProgressBar(currentIndex, nextIndex) {
    const stops = document.querySelectorAll('.stop');
    const labels = document.querySelectorAll('.label-wrapper');
    const completedSegment = document.getElementById('completed-segment');

    stops.forEach((stop, index) => {
        stop.classList.remove('highlight', 'completed');
        labels[index].classList.remove('highlight-label', 'completed-label');

        if (index < currentIndex) {
            stop.classList.add('completed');
            labels[index].classList.add('completed-label');
        } else if (index === currentIndex) {
            stop.classList.add('highlight');
            labels[index].classList.add('highlight-label');
        }
    });

    if (currentIndex >= 0) {
        const currentStop = stops[currentIndex];
        completedSegment.style.width = `${currentStop.style.left}`;
    }
}

function handleServerMessage(time) {
    serverTime = new Date(time);
    localOffset = serverTime - Date.now();
}

document.addEventListener('DOMContentLoaded', function() {
    // Получение данных остановок из контейнера
    // var stops = JSON.parse(document.getElementById('stops-data').textContent)
    // console.log('Stops data', stops);

    // Создание контейнеров динамически
    var mainContainer = document.createElement('div');
    mainContainer.className = 'main';
    document.body.appendChild(mainContainer);

    var container1 = document.createElement('div');
    container1.className = 'container-1';
    container1.id = 'container-1';
    mainContainer.appendChild(container1);

    var headerChange = document.createElement('div');
    headerChange.className = 'col-1-1-1';
    headerChange.id = 'col-1-1-1';
    container1.appendChild(headerChange);

    var headerText = document.createElement('h2');
    headerText.innerText = 'Пересадки / Change here for';
    headerChange.appendChild(headerText);

    var transitionsContainer = document.createElement('div');
    transitionsContainer.className = 'col-1-1';
    transitionsContainer.id = 'col-1-1';
    container1.appendChild(transitionsContainer);

    var container2 = document.createElement('div');
    container2.className = 'container-2';
    container2.id = 'container-2';
    mainContainer.appendChild(container2);

    var col2_1 = document.createElement('div');
    col2_1.className = 'col-2-1';
    container2.appendChild(col2_1);

    var currentStopElement = document.createElement('div');
    currentStopElement.className = 'current-stop';
    currentStopElement.id = 'current-stop';
    currentStopElement.innerText = 'Current stop: ';
    col2_1.appendChild(currentStopElement);

    var nextStopElement = document.createElement('div');
    nextStopElement.className = 'next-stop';
    nextStopElement.id = 'next-stop';
    nextStopElement.innerText = 'Next stop: ';
    col2_1.appendChild(nextStopElement);

    var col2_2 = document.createElement('div');
    col2_2.className = 'col-2-2';
    container2.appendChild(col2_2);

    var linkElement = document.createElement('link');
    linkElement.rel = 'stylesheet';
    linkElement.href = '/static/Screen_Server/CSS/moscow_map_style.css';
    col2_2.appendChild(linkElement);

    var routeElement = document.createElement('div');
    routeElement.className = 'route';
    routeElement.id = 'route';
    col2_2.appendChild(routeElement);

    var completedSegment = document.createElement('div');
    completedSegment.className = 'completed-segment';
    completedSegment.id = 'completed-segment';
    routeElement.appendChild(completedSegment);

    var container3 = document.createElement('div');
    container3.className = 'container-3';
    container3.id = 'container-3';
    mainContainer.appendChild(container3);

    var col3_1 = document.createElement('div');
    col3_1.className = 'col-3-1';
    col3_1.id = 'col-3-1';
    container3.appendChild(col3_1);

    var col3_1_1 = document.createElement('div');
    col3_1_1.className = 'col-3-1-1';
    col3_1_1.id = 'col-3-1-1';
    col3_1.appendChild(col3_1_1);

    var col3_1_1_1 = document.createElement('div');
    col3_1_1_1.className = 'col-3-1-1-1';
    col3_1_1_1.id = 'col-3-1-1-1';
    col3_1_1_1.innerText = 'Поезд следует до остановки / Terminal station:';
    col3_1_1.appendChild(col3_1_1_1);

    var col3_1_1_2 = document.createElement('div');
    col3_1_1_2.className = 'col-3-1-1-2';
    col3_1_1_2.id = 'col-3-1-1-2';
    // if (stops && stops.length > 0) {
    //     var lastStop = stops[stops.length - 1];
    //     var lastStopName = lastStop.station.name;
    //     var lastStopName2 = lastStop.station.name2;
    // }
    // col3_1_1_2.innerText = lastStopName + ' / ' + lastStopName2;
    col3_1_1.appendChild(col3_1_1_2);

    var col3_1_2 = document.createElement('div');
    col3_1_2.className = 'col-3-1-2';
    col3_1_2.id = 'col-3-1-2';
    col3_1.appendChild(col3_1_2);

    var time = document.createElement('div');
    time.className = 'time';
    time.id = 'time';
    col3_1_2.appendChild(time);

    var date = document.createElement('div');
    date.className = 'date';
    date.id = 'date';
    col3_1_2.appendChild(date);

    var col3_1_3 = document.createElement('div');
    col3_1_3.className = 'col-3-1-3';
    col3_1_3.id = 'col-3-1-3';
    col3_1.appendChild(col3_1_3);

    var temperature = document.createElement('div');
    temperature.className = 'temperature';
    temperature.id = 'temperature';
    temperature.innerText = 'температура воздуха:';
    col3_1_3.appendChild(temperature);

    var inside = document.createElement('div');
    inside.className = 'inside';
    inside.id = 'inside';
    col3_1_3.appendChild(inside);

    var insidehead = document.createElement('div');
    insidehead.className = 'insidehead';
    insidehead.id = 'insidehead';
    insidehead.innerText = 'в салоне / salon'
    inside.appendChild(insidehead);

    var insidebody = document.createElement('div');
    insidebody.className = 'insidebody';
    insidebody.id = 'insidebody';
    inside.appendChild(insidebody);

    var outside = document.createElement('div');
    outside.className = 'outside';
    outside.id = 'outside';
    col3_1_3.appendChild(outside);

    var outsidehead = document.createElement('div');
    outsidehead.className = 'outsidehead';
    outsidehead.id = 'outsidehead';
    outsidehead.innerText = 'на улице / outdoor'
    outside.appendChild(outsidehead);

    var outsidebody = document.createElement('div');
    outsidebody.className = 'outsidebody';
    outsidebody.id = 'outsidebody';
    outside.appendChild(outsidebody);

    var col3_2 = document.createElement('div');
    col3_2.className = 'col-3-2';
    col3_2.id = 'col-3-2';
    container3.appendChild(col3_2);

    function updateTime() {
        if (!serverTime) return;

        let now = new Date(Date.now() + localOffset);
        let dateOptions = {weekday: 'short', year: 'numeric', month: 'long', day: 'numeric'};
        let timeOptions = {hour: '2-digit', minute: '2-digit', second: '2-digit'};

        document.getElementById('time').innerText = now.toLocaleTimeString('ru-RU', timeOptions);
        document.getElementById('date').innerText = now.toLocaleDateString('ru-RU', dateOptions);
    }
    setInterval(updateTime, 1000);

});