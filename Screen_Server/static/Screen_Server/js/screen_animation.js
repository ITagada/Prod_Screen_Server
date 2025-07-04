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


    const socket = new WebSocket('ws://127.0.0.1:8000/ws/bnt/');

    let wagons = null;
    let side = null;
    let stops = null
    let lineColor = null;

    socket.onopen = function() {};

    socket.onmessage = function(event) {
        const packege = JSON.parse(event.data);

        if (packege.type === 'connection_data') {
            const data = packege.data;

            if (!wagons && !side) {
                wagons = data.wagons;
                side = data.side;

                console.log('Initial data: ', data);
                console.log('Line data: ', data.stops);
                console.log('Wagons: ', wagons);
                console.log('Side: ', side);

                if (wagons && wagons.length > 0) {
                    renderWagons(wagons);
                }
                if (data.stops && data.line_icons.length > 0) {
                    stops = data.stops;
                    lineColor = data.line_icons[0].color;
                    const lineIcon = data.line_icons[0].symbol;
                    const lineName = data.line_name;
                    renderLine(lineName, lineIcon, lineColor);
                    renderStops(stops, lineColor);
                }
            }
        }

        if (packege.type === 'update_station') {
            const stationData = packege.message;

            if (stationData) {
                const currentStation = stationData.current_station;
                const nextStation = stationData.next_station;
                const currentPng = stationData.current_png;

                updateRoute(currentStation, nextStation, stops);
                renderPng(currentPng);
            }
        }
    };

    socket.onerror = function(error) {
        console.log('WebSocket error:', error);
    };

    socket.onclose = function(event) {
        console.log('WebSocket connection closed');
    };

    function renderLine(lineName, lineIcon, lineColor) {
        /**
         * Отрисовывает заголовок линии с иконкой и названием.
         * @param {string} lineName - Название линии.
         * @param {string} lineIcon - Символ иконки линии.
         * @param {string} lineColor - Цвет линии в формате CSS.
         */
        lineContainer.innerHTML = '';

        const lineIconElement = document.createElement('span');
        lineIconElement.innerText = lineIcon;
        lineIconElement.style.color = lineColor;
        lineContainer.appendChild(lineIconElement);

        const lineNameContainer = document.createElement('div');
        lineNameContainer.innerText = lineName;
        lineContainer.appendChild(lineNameContainer);
    }

    function renderStops(stops, lineColor, currentStation = null) {
        /**
         * Отрисовывает остановки на прогресс-баре, создавая контейнеры с названиями и точками.
         * Опционально подсвечивает текущую станцию.
         * @param {Array} stops - Массив объектов остановок.
         * @param {string} lineColor - Цвет линии.
         * @param {Object|null} currentStation - Текущая станция (если есть).
         */
        progressBarContainer.innerHTML = '';

        const currentStationIndex = currentStation ? stops.findIndex(stop => stop.name === currentStation.name) : -1;

        // Шаг между контейнерами (расстояние между контейнерами)
        const containerPadding = 100;

        let currentX = 100;

        // Добавляем контейнеры с именами станций и точки для каждой остановки
        stops.forEach((stop, stopIndex) => {

            // Создание контейнера с именем станции
            const container = progressBarContainer.querySelector(`.stop-info[data-stop-index="${stopIndex}"]`) || createStopContainer(stop, currentStationIndex, stopIndex);

            container.style.left = `${currentX}px`;

            // if (currentStation && stop.name === currentStation.name) {
            //     container.classList.add('highlight');
            // } else {
            //     container.classList.remove('highlight');
            // }

            progressBarContainer.appendChild(container);

            const point =
                progressBarContainer.querySelector(`.stop-point[data-stop-index="${stopIndex}"]`) ||
                progressBarContainer.querySelector(`.stop-dot[data-stop-index="${stopIndex}"]`) ||
                createStopPoint(stop, lineColor, currentX, stopIndex);

            point.style.left = `${currentX}px`;

            // if (currentStation && stop.name === currentStation.name) {
            //     point.classList.add('highlight');
            // } else {
            //     point.classList.remove('highlight');
            // }

            progressBarContainer.appendChild(point);

            stop.left = currentX;
            currentX += container.offsetWidth + containerPadding;
        });

        progressBarContainer.style.width = `${currentX}px`;
        drawLine(stops[0].left, stops[stops.length - 1].left, lineColor);
    }

    function drawLine(startX, finishX, lineColor) {
        /**
         * Рисует линию прогресс-бара между стартовой и конечной остановками.
         * @param {number} startX - Координата X начала линии.
         * @param {number} finishX - Координата X конца линии.
         * @param {string} lineColor - Цвет линии.
         */
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

   function createStopContainer(stop, currentStationIndex = -1, stopIndex = -1) {
       /**
         * Создаёт DOM-элемент контейнера с информацией об остановке.
         * Добавляет иконки пересадок, если они есть и станция позже текущей.
         * @param {Object} stop - Объект остановки с полями name, name2, transfers.
         * @param {number} currentStationIndex - Индекс текущей станции.
         * @param {number} stopIndex - Индекс рассматриваемой остановки.
         * @returns {HTMLElement} - Контейнер с информацией об остановке.
         */
       const container = document.createElement('div');
       container.classList.add('stop-info');
       container.setAttribute('data-stop-index', stopIndex);
       container.style.position = 'absolute';

       const nameContainer = document.createElement('div');
       nameContainer.classList.add('name-container');
       nameContainer.innerText = stop.name;

       const name2Conatainer = document.createElement('div');
       name2Conatainer.classList.add('name2-container');
       name2Conatainer.innerText = stop.name2;

       if (currentStationIndex !== -1 && stopIndex === currentStationIndex) {
           container.appendChild(nameContainer);
           container.appendChild(name2Conatainer);
           return container;
       } else {
           container.appendChild(nameContainer);
           container.appendChild(name2Conatainer);
           if (stopIndex > currentStationIndex) {
               addTransferIcons(stop, nameContainer);
           }
           return container;
       }
   }

   function addTransferIcons(stop, nameContainer) {
       /**
         * Добавляет иконки пересадок к контейнеру имени станции.
         * Обрабатывает сложные случаи с двойными стрелками.
         * @param {Object} stop - Остановка с информацией о пересадках.
         * @param {HTMLElement} nameContainer - Контейнер имени станции.
         */
       let arrowIcons = [];

       stop.transfers.forEach(transfer => {
           transfer.icon_parts.forEach(icon => {
               if (icon.symbol === '➪' || icon.symbol === '➫') {
                   arrowIcons.push(icon);
               } else {
                   const iconSpan = document.createElement('span');
                   iconSpan.style.color = icon.color;
                   iconSpan.style.fontSize = 'clamp(0.2rem, 0.9vw + 0.5rem, 3rem)';
                   iconSpan.innerText = " " + icon.symbol;
                   nameContainer.appendChild(iconSpan);
               }
           });
       });

       if (arrowIcons.length === 2) {
           const combinedIcon = document.createElement('span');
           combinedIcon.style.position = 'relative';

           const icon1 = document.createElement('span');
           icon1.style.color = arrowIcons[0].color;
           icon1.style.fontSize = 'clamp(0.2rem, 0.9vw + 0.5rem, 3rem)';
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
               iconSpan.innerText = icon.symbol;
               nameContainer.appendChild(iconSpan);
           });
       }
   }

   function createStopPoint(stop, lineColor, currentX, stopIndex) {
       /**
         * Создаёт визуальную точку на прогресс-баре для остановки.
         * Точка меняет стиль в зависимости от наличия пересадок.
         * @param {Object} stop - Объект остановки.
         * @param {string} lineColor - Цвет линии.
         * @param {number} currentX - Координата по горизонтали.
         * @param {number} stopIndex - Индекс остановки.
         * @returns {HTMLElement} - Элемент точки остановки.
         */
       const point = document.createElement('div');
       const hasTransfer = stop.transfers.some(transfer => transfer.transfer_name !== '');

       if (hasTransfer) {
           point.classList.add('stop-point');
           point.style.borderColor = lineColor;
       } else {
           point.classList.add('stop-dot');
           point.style.backgroundColor = lineColor;
       }

       point.style.position = 'absolute';
       point.setAttribute('data-stop-index', stopIndex);
       point.style.left = `${currentX}px`;
       return point;
   }

    function updateRoute(currentStation, nextStation, stops) {
       /**
         * Обновляет маршрут: анимирует сдвиг прогресс-бара, подсвечивает текущую станцию.
         * @param {Object} currentStation - Текущая станция.
         * @param {Object} nextStation - Следующая станция.
         * @param {Array} stops - Массив всех остановок.
         */
        const currentStationIndex = stops.findIndex(stop => stop.name === currentStation.name);
        const nextStationIndex = stops.findIndex(stop => stop.name === nextStation.name);

        if (currentStationIndex === -1 || nextStationIndex === -1) return;

        // Получаем элементы текущей и следующей станции
        const currentStationElement = progressBarContainer.querySelectorAll('.stop-info')[currentStationIndex];
        const nextStationElement = progressBarContainer.querySelectorAll('.stop-info')[nextStationIndex];

        // Определяем целевое положение для текущей остановки
        const targetPosition = 100; // Например, 100 пикселей от левого края экрана

        // Рассчитываем текущее смещение для прогресс-бара
        const currentStationOffset = currentStationElement.getBoundingClientRect().left;
        const progressBarOffset = progressBarContainer.getBoundingClientRect().left; // Положение прогресс-бара

        const nameContainer = currentStationElement.querySelector('.name-container');

        Promise.all([
            animateProgressBarShift(targetPosition, currentStationOffset, progressBarOffset),
            highlightCurrentStation(currentStation, stops)
        ]).then(() => {
            setTimeout(() => {
                renderStops(stops, lineColor, currentStation);
            }, 500);
        });
    }

    function animateProgressBarShift(targetPosition, currentStationOffset, progressBarOffset) {
       /**
         * Анимирует плавный сдвиг прогресс-бара к целевой позиции.
         * @param {number} targetPosition - Целевая позиция по оси X.
         * @param {number} currentStationOffset - Текущая координата текущей станции.
         * @param {number} progressBarOffset - Координата прогресс-бара.
         * @returns {Promise} - Промис, разрешающийся после завершения анимации.
         */
       return new Promise((resolve) => {
           const shiftX = targetPosition - (currentStationOffset - progressBarOffset);
           const start = performance.now();
           const startX = parseFloat(getComputedStyle(progressBarContainer).transform.split(',')[4]) || 0;

           function animate(timestamp) {
               const progress = Math.min ((timestamp - start) / 500, 1);
               const currentX = startX + (shiftX - startX) * progress;

               progressBarContainer.style.transform = `translateX(${currentX}px)`;
               progressLine.style.transform = `translateX(${currentX}px)`;

               if (progress < 1) {
                   requestAnimationFrame(animate);
               } else {
                   resolve();
               }
           }
           requestAnimationFrame(animate);
       });
    }

   function animateSpansOut(nameContainer) {
       /**
         * Анимирует скрытие span-элементов в контейнере имени станции.
         * Возвращает промис, который резолвится после окончания анимаций.
         * @param {HTMLElement} nameContainer - Контейнер имени станции.
         * @returns {Promise}
         */
       return new Promise((resolve) => {
           const spans = nameContainer.querySelectorAll('span');
           let animationsCompleted = 0;

           spans.forEach(span => {
               // Восстанавливаем видимость и положение перед анимацией
               span.style.opacity = '1';
               span.style.transform = 'translateX(0)';
               span.style.transition = 'opacity 0.5s ease, transform 0.5s ease';
               span.style.position = 'static';

               span.addEventListener('transitionend', () => {
                   animationsCompleted++;
                   if (animationsCompleted === spans.length) {
                       resolve();
                   }
               }, {once: true});
           });
       });
   }

    function animateSpans(nameContainer) {
       /**
         * Анимирует появление span-элементов в контейнере имени станции.
         * Возвращает промис, который резолвится после окончания анимаций.
         * @param {HTMLElement} nameContainer - Контейнер имени станции.
         * @returns {Promise}
         */
       return new Promise((resolve) => {
           const spans = nameContainer.querySelectorAll('span');
           let animationsCompleted = 0;

           spans.forEach(span => {
               span.style.opacity = '0';
               span.style.transform = 'translateX(-100%)';
               span.style.transition = 'opacity 0.5s ease, transform 0.5s ease';
               span.style.position = 'absolute';
               span.style.left = '100%';

               span.addEventListener('transitionend', () => {
                   animationsCompleted++;
                   if (animationsCompleted === spans.length) {
                       resolve();
                   }
               }, {once: true});
           });
       });
    }

    function toggleHighlight(nameContainer, highlight) {
       /**
         * Переключает подсветку имени станции с анимацией.
         * Если highlight true — анимирует появление, иначе — скрытие.
         * @param {HTMLElement} nameContainer - Контейнер имени станции.
         * @param {boolean} highlight - Флаг подсветки.
         * @returns {Promise}
         */
       if (highlight) {
           return animateSpans(nameContainer);
       } else {
           return animateSpansOut(nameContainer);
       }
    }

    function highlightCurrentStation(currentStation, stops) {
       /**
         * Подсвечивает текущую станцию на прогресс-баре.
         * Снимает подсветку с других станций.
         * @param {Object} currentStation - Текущая станция.
         * @param {Array} stops - Массив остановок.
         * @returns {Promise}
         */
        return new Promise((resolve) => {
            const currentStationIndex = stops.findIndex(stop => stop.name === currentStation.name);
            if (currentStationIndex === -1) return resolve();

            // Находим все точки остановок
            const stopPoints = progressBarContainer.querySelectorAll('.stop-point, .stop-dot');
            const stopInfos = progressBarContainer.querySelectorAll('.stop-info');

            // Удаляем эффект увеличения с других точек
            stopPoints.forEach(point => point.classList.remove('highlight'));
            stopInfos.forEach(stopInfo => {
                const nameContainer = stopInfo.querySelector('.name-container');
                const name2Container = stopInfo.querySelector('.name2-container');

                // Скрываем элементы в контейнере, если убираем highlight
                toggleHighlight(nameContainer, false);

                stopInfo.classList.remove('highlight');
                nameContainer.classList.remove('highlight');
                name2Container.classList.remove('highlight');
            });

            // Анимация для текущей станции
            const currentStopInfo = stopInfos[currentStationIndex];
            const currentStopPoint = stopPoints[currentStationIndex];

            if (currentStopInfo) {
                const nameContainer = currentStopInfo.querySelector('.name-container');
                const name2Container = currentStopInfo.querySelector('.name2-container');

                // 1. Добавляем highlight и показываем span-ы
                if (currentStopPoint) {
                    currentStopInfo.classList.add('highlight');
                    currentStopPoint.classList.add('highlight');
                }

                nameContainer.classList.add('highlight');
                name2Container.classList.add('highlight');

                Promise.all([
                    toggleHighlight(nameContainer, true)
                ]).then(() => {
                    setTimeout(() => {
                        renderStops(stops, lineColor, currentStation);
                        resolve();
                    }, 500);
                });
            }
        });
    }

    function renderWagons(wagons) {
       /**
         * Отрисовывает изображения вагонов в нижнем контейнере.
         * Если контейнер вагонов отсутствует — создаёт новый.
         * @param {Array} wagons - Массив объектов вагонов с base64-строкой изображения.
         */
        let wagonsContainer = document.querySelector('.wagons-container');

        if (wagonsContainer) {
            wagonsContainer.innerHTML = '';
        } else {
            wagonsContainer = document.createElement('div');
            wagonsContainer.classList.add('wagons-container');

            wagonsContainer.style.position = 'absolute';
            wagonsContainer.style.bottom = '2%';
            wagonsContainer.style.width = '90%';
            wagonsContainer.style.left = '50%';
            wagonsContainer.style.gap = '0.5%';
            wagonsContainer.style.transform = 'translateX(-50%)';
            wagonsContainer.style.display = 'flex';
            wagonsContainer.style.justifyContent = 'space-around';
            wagonsContainer.style.alignItems = 'center';
            wagonsContainer.style.overflow = 'hidden';

            bottomContainer.appendChild(wagonsContainer);
        }

        wagons.forEach(wagon => {
            const wagonImg = document.createElement('img');
            wagonImg.src = `data:image/png;base64,${wagon.encoded_string}`;
            wagonImg.alt = wagon.name;
            wagonImg.style.maxWidth = '100%';
            wagonImg.style.maxHeight = '100%';
            wagonImg.style.objectFit = 'contain';

            const wagonWrapper = document.createElement('div');
            wagonWrapper.style.flex = '1';
            wagonWrapper.style.display = 'flex';
            wagonWrapper.style.justifyContent = 'center';
            wagonWrapper.style.alignItems = 'center';

            wagonWrapper.appendChild(wagonImg);
            wagonsContainer.appendChild(wagonWrapper);
        })
    }

    function renderPng(currentPng) {
       /**
         * Отрисовывает PNG-схему текущей станции как фон в нижнем контейнере.
         * Если изображения нет — выводит предупреждение.
         * @param {string} currentPng - Base64-код PNG-изображения.
         */
       if (!currentPng) {
           console.warn("No image data available for current station.");
           return
       }

       let schemaContainer = bottomContainer.querySelector('.schema-container');
       if (!schemaContainer) {
           schemaContainer = document.createElement('div');
           schemaContainer.classList.add('schema-container');
           bottomContainer.appendChild(schemaContainer);
       }

       // Преобразуем PNG в URL
       const imageUrl = `data:image/png;base64,${currentPng}`;
       // Устанавливаем изображение как фон для schema-container
       schemaContainer.style.backgroundImage = `url(${imageUrl})`;
       schemaContainer.style.backgroundSize = '100% 100%';    // Подгоняет изображение под размеры контейнера, сохраняя пропорции
       schemaContainer.style.backgroundPosition = 'center'; // Центрирует изображение
       schemaContainer.style.backgroundRepeat = 'no-repeat'; // Не повторяет изображение

       // Задаем стили для schema-container, чтобы он занимал нужное пространство в bottom-container
       schemaContainer.style.position = 'absolute';
       schemaContainer.style.top = '0';
       schemaContainer.style.left = '0';
       schemaContainer.style.width = '100%';
       schemaContainer.style.height = '100%';
       schemaContainer.style.zIndex = '-1';
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