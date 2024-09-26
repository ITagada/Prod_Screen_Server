
const topContainer = document.getElementById('top-container');
const bottomContainer = document.getElementById('bottom-container');
const progressBarContainer = document.getElementById('progress-bar-container');
const trigger = document.getElementById('trigger');
let isVisible = true;

function renderStops(stops) {
    progressBarContainer.innerHTML = '';

    let currentLeftOffset = 0;
    const fixedSpacing = 50;

    stops.forEach((stop, index) => {
        const stopMarker = document.createElement('div');
        stopMarker.classList.add('stop-marker');
        stopMarker.style.left = `${currentLeftOffset}px`;
        progressBarContainer.appendChild(stopMarker);

        const stopInfo = document.createElement('div');
        stopInfo.classList.add('stop-info');
        stopInfo.innerText = stop.name;
        stopInfo.style.left = `${currentLeftOffset}px`
        progressBarContainer.appendChild(stopInfo);

        const stopInfoWidth = stopInfo.offsetWidth;

        currentLeftOffset += stopInfoWidth + fixedSpacing;

        const stopMarkers = document.querySelectorAll('.stop-marker');
        const progressBarBackgroundColor = getComputedStyle(progressBarContainer).backgroundColor;

        stopMarkers.forEach(marker => {
            marker.style.borderColor = progressBarBackgroundColor;
        });
    });

    window.addEventListener('resize', () => {
        let updatedLeftOffset = 0;

        stops.forEach((stop, index) => {
            const stopInfo = progressBarContainer.querySelectorAll('.stop-info')[index];
            const stopMarker = progressBarContainer.querySelectorAll('.stop-marker')[index];

            const updatedStopInfoWidth = stopInfo.offsetWidth;

            stopMarker.style.left = `${updatedLeftOffset}px`;
            stopInfo.style.left = `${updatedLeftOffset}px`;

            updatedLeftOffset += updatedStopInfoWidth + fixedSpacing;
        })
    })
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
    } else {
        // Показываем контейнеры
        topContainer.style.transform = 'translateY(0)';
        bottomContainer.style.transform = 'translateY(100%)';
        progressBarContainer.classList.remove('attached-to-bottom');
    }
    isVisible = !isVisible;
});

const socket = new WebSocket('ws://127.0.0.1:8000/ws/bnt/');

socket.onopen = function() {
    // console.log('WebSocket connection established');
    // socket.send(JSON.stringify({action: 'get_stops'}));
};

socket.onmessage = function(event) {
    const data = JSON.parse(event.data);
    console.log('Opened data: ', data);

    if (data.stops) {
        renderStops(data.stops);
    }
};

socket.onerror = function(error) {
    console.log('WebSocket error:', error);
};

socket.onclose = function(event) {
    console.log('WebSocket connection closed');
};