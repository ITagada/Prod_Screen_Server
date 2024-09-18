
const topContainer = document.getElementById('top-container');
const bottomContainer = document.getElementById('bottom-container');
const progressBarContainer = document.getElementById('progress-bar-container');
const trigger = document.getElementById('trigger');
let isVisible = true;

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