document.addEventListener('DOMContentLoaded', () => {

    const topContainer = document.getElementById('top-container');
    const bottomContainer = document.getElementById('bottom-container');
    const progressBarContainer = document.getElementById('progress-bar-container');
    const progressLine = document.getElementById('progress-line');
    const trigger = document.getElementById('trigger');
    let isVisible = true;
    let stops = [];
    let lineColor = null;


    const socket = new WebSocket('ws://127.0.0.1:8000/ws/bnt/');

    socket.onopen = function() {
        // console.log('WebSocket connection established');
        // socket.send(JSON.stringify({action: 'get_stops'}));
    };

    socket.onmessage = function(event) {
        const data = JSON.parse(event.data);
        console.log('Opened data: ', data);

        if (data.stops && data.line_icons.length > 0) {
            stops = data.stops;
            lineColor = data.line_icons[0].color;
            renderStops(stops, lineColor);
        }

        if (data.type === 'update_station' && data.message) {
            const currentStation = data.message.current_station;
            updateRoute(currentStation, stops);
        }
    };

    socket.onerror = function(error) {
        console.log('WebSocket error:', error);
    };

    socket.onclose = function(event) {
        console.log('WebSocket connection closed');
    };


    function renderStops(stops, lineColor) {
        // Очистка progressBarContainer перед отрисовкой
        progressBarContainer.innerHTML = '';

        // Шаг между контейнерами (расстояние между контейнерами)
        const containerPadding = 50;

        let currentX = 0;

        // Добавляем контейнеры с именами станций и точки для каждой остановки
        stops.forEach((stop, index) => {
            // Создание контейнера с именем станции
            const container = document.createElement('div');
            container.classList.add('stop-info');
            container.innerText = stop.name; // Название станции
            container.style.left = `${currentX}px`; // Позиция контейнера по оси X
            progressBarContainer.appendChild(container);

            // Создание точки
            const point = document.createElement('div');

            const hasTransfer = stop.transfers.some(transfer => transfer.transfer_name !== '');
            if (hasTransfer) {
                point.classList.add('stop-point');
                point.style.left = `${currentX}px`; // Позиция точки по оси X (та же, что и у контейнера)
                point.style.borderColor = lineColor;
                progressBarContainer.appendChild(point);
            } else {
                point.classList.add('stop-dot');
                point.style.left = `${currentX}px`;
                point.style.backgroundColor = lineColor;
                progressBarContainer.appendChild(point);
            }

            currentX += container.offsetWidth + containerPadding;
        });

        // Устанавливаем ширину progressBarContainer
        progressBarContainer.style.width = `${currentX}px`;

        drawLine(stops, lineColor);
    }

   function drawLine(stops, lineColor) {
        if (stops.length === 0) {
            progressLine.style.width = '0';
            return;
        }

        const allContainers = document.querySelectorAll('.stop-info');
        const searchStart = stops[0].name;
        const searchFinish = stops[stops.length - 1].name;

        const startContainer = Array.from(allContainers).find(container =>
            container.textContent.includes(searchStart)
        );

        const finishContainer = Array.from(allContainers).find(container =>
            container.textContent.includes(searchFinish)
        );

        const startRect = startContainer.getBoundingClientRect();
        const startX = startRect.left + window.scrollX + 2;

        const finishRect = finishContainer.getBoundingClientRect();
        const finishX = finishRect.left + window.scrollX + 2;

        const lineLenght = finishX - startX;
        progressLine.style.width = `${lineLenght}px`;
        progressLine.style.left = `${startX}px`;
        progressLine.style.backgroundColor = lineColor;
    }

    // Обработчик события изменения размера окна
   window.addEventListener('resize', () => {
       // Перерисовка остановок при изменении размера окна
       renderStops(stops, lineColor);
   });

   function updateRoute(currentStation, stops) {
       const currentStationIndex = stops.findIndex(stop => stop.name === currentStation.name);

       if (currentStationIndex === -1) return;

       let offsetToCurrentStation = 0;

       for (let i = 0; i < currentStationIndex; i++) {
           const stopInfo = progressBarContainer.querySelectorAll('.stop-info')[i];
           offsetToCurrentStation -= (stopInfo.offsetWidth + 50)
       }

       // Получаем текущее смещение
        const startX = parseFloat(getComputedStyle(progressBarContainer).transform.split(',')[4]) || 0;
        const startLineX = parseFloat(getComputedStyle(progressLine).transform.split(',')[4]) || 0;

        // Определяем целевое смещение
        const targetX = offsetToCurrentStation;

        // Плавная анимация с использованием requestAnimationFrame
        const animate = (timestamp) => {
            const progress = Math.min((timestamp - start) / 500, 1); // 500 мс для анимации
            const currentX = startX + (targetX - startX) * progress;

            progressBarContainer.style.transform = `translateX(${currentX}px)`;
            progressLine.style.transform = `translateX(${currentX}px)`;

            if (progress < 1) {
                requestAnimationFrame(animate);
            }
        };

        const start = performance.now(); // Начало анимации
        requestAnimationFrame(animate);
        highlightCurrentStation(currentStation, stops);
   }

   function highlightCurrentStation(currentStation, stops) {
        const currentStationIndex = stops.findIndex(stop => stop.name === currentStation.name);
        if (currentStationIndex === -1) return;

        // Находим все точки остановок
        const stopPoints = progressBarContainer.querySelectorAll('.stop-point, .stop-dot');

        // Удаляем эффект увеличения с других точек
        stopPoints.forEach(point => {
            point.classList.remove('highlight');
        });

        // Находим точку текущей станции и добавляем эффект
        const currentStopPoint = stopPoints[currentStationIndex];
        if (currentStopPoint) {
            currentStopPoint.classList.add('highlight');
        }
   }


    setTimeout(() => {
        topContainer.style.transform = 'translateY(0)';
        bottomContainer.style.transform = 'translateY(100%)';
    }, 50);

    trigger.addEventListener('click', () => {
        if (isVisible) {
            // Прячем контейнеры
            topContainer.style.transform = 'translateY(-100%)';
            bottomContainer.style.transform = 'translateY(0)';
            progressBarContainer.classList.add('attached-to-bottom');
            progressLine.classList.add('attached-to-bottom');

        } else {
            // Показываем контейнеры
            topContainer.style.transform = 'translateY(0)';
            bottomContainer.style.transform = 'translateY(100%)';
            progressBarContainer.classList.remove('attached-to-bottom');
            progressLine.classList.remove('attached-to-bottom');
        }
        isVisible = !isVisible;
    });
});