/**
 * Admin Test Print Handler
 *
 * Handles click events for test print buttons in the Django Admin interface.
 * Sends a POST request with a JSON payload containing 'color' and 'duplex' parameters.
 */

document.addEventListener('DOMContentLoaded', function() {
    // Select all test print action buttons
    const testPrintButtons = document.querySelectorAll('.admin-test-print-btn');

    /**
     * Helper function to retrieve a cookie value by name (used for CSRF token).
     *
     * @param {string} name - The name of the cookie.
     * @returns {string|null} The cookie value or null if not found.
     */
    function getCookie(name) {
        let cookieValue = null;
        if (document.cookie && document.cookie !== '') {
            const cookies = document.cookie.split(';');
            for (let i = 0; i < cookies.length; i++) {
                const cookie = cookies[i].trim();
                if (cookie.substring(0, name.length + 1) === (name + '=')) {
                    cookieValue = decodeURIComponent(cookie.substring(name.length + 1));
                    break;
                }
            }
        }
        return cookieValue;
    }

    testPrintButtons.forEach(button => {
        button.addEventListener('click', function(event) {
            event.preventDefault();
            event.stopPropagation();

            const url = this.getAttribute('data-url');
            const color = this.getAttribute('data-color') === 'true';
            const duplex = this.getAttribute('data-duplex') === 'true';

            const csrfInput = document.querySelector('[name=csrfmiddlewaretoken]');
            const csrftoken = csrfInput ? csrfInput.value : getCookie('csrftoken');

            const payload = {
                color: color,
                duplex: duplex
            };

            console.log('Sending test print request:', { url, payload });

            fetch(url, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    'X-CSRFToken': csrftoken
                },
                body: JSON.stringify(payload)
            })
            .then(response => {
                console.log('Response status:', response.status);
                return response.json();
            })
            .then(data => {
                console.log('Response data:', data);

                if (data.status === 'ok') {
                    // Success — display alert and reload page
                    alert(`Test print job #${data.job_id} successfully dispatched!`);
                    setTimeout(() => {
                        window.location.reload();
                    }, 500);
                } else {
                    // Error response — display error details
                    const errorMessage = data.message || 'Unknown error';
                    const details = data.details ? `\n\nDetails: ${data.details}` : '';
                    alert(`Test print failed: ${errorMessage}${details}`);
                }
            })
            .catch(error => {
                console.error('Error during test print request:', error);
                alert(`Network error: ${error.message}`);
            });
        });
    });
});
