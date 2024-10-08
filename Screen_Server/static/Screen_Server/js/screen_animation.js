document.addEventListener('DOMContentLoaded', () => {

    const topContainer = document.getElementById('top-container');
    const bottomContainer = document.getElementById('bottom-container');
    const progressBarContainer = document.getElementById('progress-bar-container');
    const progressLine = document.getElementById('progress-line');
    const trigger = document.getElementById('trigger');
    const speedContainer = document.getElementById('speed-container');
    const timeContainer = document.getElementById('time-container');
    const temperatureContainer = document.getElementById('temperature-container');
    const lineContainer = document.getElementById('line-container');
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
            const lineIkon = data.line_icons[0].symbol;
            const lineName = data.line_name;
            renderLine(lineName, lineIkon, lineColor);
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

    function renderLine(lineName, lineIcon, lineColor) {
        lineContainer.innerHTML = '';

        const lineIconElement = document.createElement('span');
        lineIconElement.innerText = lineIcon;
        lineIconElement.style.color = lineColor;
        lineContainer.appendChild(lineIconElement);

        const lineNameContainer = document.createElement('div');
        lineNameContainer.innerText = lineName;
        lineContainer.appendChild(lineNameContainer);
    }

    function renderStops(stops, lineColor) {
        // Очистка progressBarContainer перед отрисовкой
        progressBarContainer.innerHTML = '';

        // Шаг между контейнерами (расстояние между контейнерами)
        const containerPadding = 100;

        let currentX = 30;

        // Добавляем контейнеры с именами станций и точки для каждой остановки
        stops.forEach((stop, index) => {

            // Создание контейнера с именем станции
            const container = document.createElement('div');
            container.classList.add('stop-info');

            const nameContainer = document.createElement('div');
            nameContainer.classList.add('name-container');
            nameContainer.innerText = stop.name;
            container.appendChild(nameContainer);

            const name2Container = document.createElement('div');
            name2Container.classList.add('name2-container');
            name2Container.innerText = stop.name2;
            container.appendChild(name2Container);

            let arrowIcons =[];

            // Добавляем иконки из подмассива transfers.icon_parts, если они есть
            stop.transfers.forEach(transfer => {
                transfer.icon_parts.forEach(icon => {
                    if (icon.symbol === '➪' || icon.symbol === '➫') {
                        arrowIcons.push(icon);
                    } else {
                        // Создаем элемент span для каждой иконки
                        const iconSpan = document.createElement('span');
                        iconSpan.style.color = icon.color;  // Задаем цвет иконки
                        iconSpan.innerText = " " + icon.symbol;   // Добавляем символ иконки

                        // Добавляем иконку к stationContent
                        nameContainer.appendChild(iconSpan);
                    }
                });
            });

            if (arrowIcons.length === 2) {
                const combinedIcon = document.createElement('span');
                combinedIcon.style.position = 'relative';

                const icon1 = document.createElement('span');
                icon1.style.color = arrowIcons[0].color;
                icon1.innerText = arrowIcons[0].symbol;
                combinedIcon.appendChild(icon1);

                const icon2 = document.createElement('span');
                icon2.style.color = arrowIcons[1].color;
                icon2.innerText = arrowIcons[1].symbol;
                icon2.style.position = 'absolute';
                icon2.style.top = '0';
                icon2.style.left = '0';
                combinedIcon.appendChild(icon2);

                nameContainer.appendChild(combinedIcon);
            } else {
                arrowIcons.forEach(icon => {
                    const iconSpan = document.createElement('span');
                    iconSpan.style.color = icon.color;
                    iconSpan.innerText = " " + icon.symbol;
                    nameContainer.appendChild(iconSpan);
                });
            }

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

            stop.left = currentX;

            currentX += container.offsetWidth + containerPadding;
        });

        // Устанавливаем ширину progressBarContainer
        progressBarContainer.style.width = `${currentX}px`;

        const startX = stops[0].left;
        const finishX = stops[stops.length - 1].left;
        drawLine(startX, finishX, lineColor);
    }

    function drawLine(startX, finishX, lineColor) {
        if (finishX - startX <= 0) {
            progressLine.style.width = '0';
            console.warn('Have not points to start and finish');
            return;
        }

        const lineLength = finishX - startX;
        progressLine.style.width = `${lineLength}px`;
        progressLine.style.left = `${startX}px`;
        progressLine.style.backgroundColor = lineColor;
    }

   let resizeTimeout;

    // Обработчик события изменения размера окна
   window.addEventListener('resize', () => {
       // Перерисовка остановок при изменении размера окна
       clearTimeout(resizeTimeout);
       resizeTimeout = setTimeout(() => {
           renderStops(stops, lineColor);
       }, 200);
   });

   function updateRoute(currentStation, stops) {
       const currentStationIndex = stops.findIndex(stop => stop.name === currentStation.name);

       if (currentStationIndex === -1) return;

       let offsetToCurrentStation = 30;

       for (let i = 0; i < currentStationIndex; i++) {
           const stopInfo = progressBarContainer.querySelectorAll('.stop-info')[i];
           offsetToCurrentStation -= (stopInfo.offsetWidth + 100)
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
        const stopInfos = progressBarContainer.querySelectorAll('.stop-info');

        // Удаляем эффект увеличения с других точек
        stopPoints.forEach(point => {
            point.classList.remove('highlight');
        });
        stopInfos.forEach(stopInfo => {
            const nameContainer = stopInfo.querySelector('.name-container');
            const name2Container = stopInfo.querySelector('.name2-container');

            nameContainer.classList.remove('highlight');
            name2Container.classList.remove('highlight');

            const spans = nameContainer.querySelectorAll('span');
            spans.forEach(span => {
                span.style.transform = 'translateX(100%)';
                span.style.opacity = '1';
                span.style.transition = 'transform 0.5s ease, opacity 0.5s ease';
            })
        })

        // Находим точку текущей станции и добавляем эффект
        const currentStopPoint = stopPoints[currentStationIndex];
        const currentStopInfo = stopInfos[currentStationIndex];

        if (currentStopPoint) {
            currentStopPoint.classList.add('highlight');
        }

        if (currentStopInfo) {
            const nameContainer = currentStopInfo.querySelector('.name-container');
            const name2Container = currentStopInfo.querySelector('.name2-container');

            nameContainer.classList.add('highlight');
            name2Container.classList.add('highlight');

            if (nameContainer.classList.contains('highlight')) {
                const spans = nameContainer.querySelectorAll('span');
                spans.forEach(span => {
                    const spanWidth = span.offsetWidth;
                    if (spanWidth > 0) {
                        span.style.transform = `translateX(${spanWidth}px)`;
                        span.style.opacity = '0';
                        span.style.transition = 'transform 0.5s ease, opacity 0.5s ease';
                    }
                });
            }
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
            topContainer.classList.add('hidden-top-container');
        } else {
            // Показываем контейнеры
            topContainer.style.transform = 'translateY(0)';
            bottomContainer.style.transform = 'translateY(100%)';
            progressBarContainer.classList.remove('attached-to-bottom');
            progressLine.classList.remove('attached-to-bottom');
            topContainer.classList.remove('hidden-top-container');
        }
        isVisible = !isVisible;
    });
});