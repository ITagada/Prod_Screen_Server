
//Скрипт получения информации о конечном устройстве

document.addEventListener('DOMContentLoaded', () => {
    try {
        let screenWidth = window.screen.width;
        let screenHeight = window.screen.height;

        console.log(screenWidth);
        console.log(screenHeight);

        const csrfTokenElement = document.querySelector('[name=csrfmiddlewaretoken]');
        if (csrfTokenElement) {
            const csrfToken = csrfTokenElement.value;

            fetch('', {
                method: "POST",
                headers: {
                    'Content-Type': 'application/json',
                    'X-CSRFToken': csrfToken
                },
                body: JSON.stringify({
                    screen_width: screenWidth,
                    screen_height: screenHeight
                })
            }).then(response => {
                if (!response.ok) {
                    throw new Error('Network response was not ok ' + response.statusText);
                }
                return response.json();
            }).then(data => {
                console.log(data);
                if (data.redirect_url) {
                    window.location.href = data.redirect_url;
                }
            }).catch(error => {
                console.error('There was a problem with the fetch operation: ', error);
            });
        } else {
            console.error('CSRF token not found');
        }
    } catch (error) {
        console.error('Error in script execution:', error);
    }
});
