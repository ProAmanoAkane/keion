document.addEventListener('DOMContentLoaded', () => {
    // WebSocket setup
    // setupWebSocket(); // Consider if WS is still needed with polling, or enhance it

    // Set up auto-refresh for components using polling
    setupAutoRefresh();

    // Set up form handling (for add song form)
    setupFormHandling();

    // Set up error handling for player control buttons
    setupPlayerErrorHandling(); // Added this call

    setupThemeToggle(); // Add this line
});

function setupAutoRefresh() {
    const playersContainer = document.getElementById('players-container');
    const statsContainer = document.getElementById('stats-container');

    const updateComponents = () => {
        // Use htmx.ajax for finer control if needed, or rely on hx-trigger polling
        // If using hx-trigger="every 5s" on the containers, this manual JS interval might be redundant.
        // Let's keep it for clarity, assuming containers might not have hx-trigger themselves.
        if (playersContainer) {
             // Request the component directly
             htmx.ajax('GET', '/components/players', { target: playersContainer, swap: 'innerHTML' });
        }
         if (statsContainer) {
             htmx.ajax('GET', '/components/stats', { target: statsContainer, swap: 'innerHTML' });
         }
    };

    // Initial load
    updateComponents();

    // Refresh every 5 seconds (adjust interval as needed)
    const refreshInterval = setInterval(updateComponents, 5000);

    // Optional: Clear interval if the page is hidden to save resources
    document.addEventListener('visibilitychange', () => {
        if (document.hidden) {
            // clearInterval(refreshInterval); // Decide if pausing updates is desired
        } else {
            // If paused, restart interval or trigger immediate update
             // refreshInterval = setInterval(updateComponents, 5000);
             updateComponents(); // Refresh immediately when tab becomes visible
        }
    });


    // Button click visual feedback (loading state) - Handles any hx-post button
    document.body.addEventListener('htmx:beforeRequest', (e) => {
         if (e.detail.elt.tagName === 'BUTTON' && e.detail.requestConfig.verb === 'post') {
             const button = e.detail.elt;
             button.classList.add('opacity-50', 'cursor-not-allowed');
             button.disabled = true;
         }
     });

     document.body.addEventListener('htmx:afterRequest', (e) => {
          if (e.detail.elt.tagName === 'BUTTON' && e.detail.requestConfig.verb === 'post') {
              const button = e.detail.elt;
              // Remove loading state regardless of success or failure
              button.classList.remove('opacity-50', 'cursor-not-allowed');
              button.disabled = false;
              // No automatic component update here - let polling handle it or trigger explicitly if needed
          }
      });
}

function setupFormHandling() {
    // Handle Add Song form specifically
     htmx.on('htmx:afterRequest', (event) => {
         // Check if it was the add song request and it was successful
         if (event.detail.pathInfo.requestPath === '/api/player/add' && event.detail.successful) {
             const form = event.detail.elt.closest('form'); // Find the parent form
             if (form) {
                 form.reset(); // Clear the form fields
             }

             // Show feedback from the success response
             try {
                  const response = JSON.parse(event.detail.xhr.response);
                  showToast(response.message || "Song added successfully!", 'success'); // Use response message
             } catch(e) {
                  showToast("Song added successfully!", 'success'); // Fallback message
             }

              // Optionally trigger an immediate refresh of players after adding
             // setTimeout(() => {
             //     htmx.ajax('GET', '/components/players', {target: '#players-container'});
             // }, 500); // Delay slightly
         }
          // Note: Error handling for the add form might be needed here too,
          // or rely on the generic responseError handler if the form uses hx-target for errors.
     });
}


function setupPlayerErrorHandling() {
    htmx.on('htmx:responseError', (event) => {
        console.log("Response Error Event:", event.detail); // Debugging

        // Check if the error came from a player control request
         // Ensure pathInfo exists and has the requestPath property
        const requestPath = event.detail.pathInfo?.requestPath;
        if (requestPath?.startsWith('/api/player/') && requestPath.includes('/control/')) {
            const xhr = event.detail.xhr;
            let errorMessage = 'An unknown error occurred.';

            // Try to parse the JSON response for a 'detail' field
            try {
                const response = JSON.parse(xhr.responseText);
                 if (response?.detail) { // FastAPI errors often use 'detail'
                    errorMessage = response.detail;
                } else if (response?.message) { // Check for 'message' if you use that
                     errorMessage = response.message;
                 } else {
                     errorMessage = `Error ${xhr.status}: ${xhr.statusText || 'Server Error'}`;
                 }
            } catch (e) {
                // If response is not JSON or empty
                 errorMessage = `Error ${xhr.status}: ${xhr.statusText || 'Server Error'}`;
            }

            // Find the target error div (which should have been set via hx-target on the button)
            const errorTarget = event.detail.target; // HTMX sets event.detail.target to the element specified in hx-target
            console.log("Error Target:", errorTarget); // Debugging

            if (errorTarget) {
                 // Display the error message inside the target element
                 errorTarget.innerHTML = ''; // Clear previous errors
                 const errorSpan = document.createElement('span');
                 errorSpan.textContent = errorMessage;
                 errorSpan.className = 'text-red-500 text-sm fade-in'; // Add animation class if desired
                 errorTarget.appendChild(errorSpan);

                 // Clear the error after a few seconds
                 setTimeout(() => {
                      if (errorTarget.contains(errorSpan)) { // Check if still the same error
                          errorTarget.innerHTML = '';
                      }
                 }, 5000); // 5 seconds
            } else {
                 // Fallback: Show a toast if no specific target was found (shouldn't happen if hx-target is set)
                 console.warn("No hx-target found for player control error display. Showing toast instead.");
                 showToast(`Player Action Failed: ${errorMessage}`, 'error');
             }
        } else if (requestPath === '/api/player/add') {
             // Handle errors specifically for the add song form if needed
             // This might duplicate the generic htmx:responseError if the form also uses it.
             const xhr = event.detail.xhr;
             let errorMessage = 'Failed to add song.';
             try {
                  const response = JSON.parse(xhr.responseText);
                  errorMessage = response.message || response.detail || errorMessage;
              } catch (e) {
                  errorMessage = `Error ${xhr.status}: ${xhr.statusText || 'Could not add song'}`;
              }
              showToast(errorMessage, 'error'); // Show error as toast for add song form
        }
    });
}


function showToast(message, type = 'success') {
    const toastContainer = document.getElementById('toast-container') || createToastContainer();

    const toast = document.createElement('div');
    const baseClasses = 'px-4 py-2 rounded-lg shadow-md text-white mb-2 transition-all duration-300 ease-in-out transform';
    const typeClasses = type === 'success' ? 'bg-green-600' : 'bg-red-600';
    toast.className = `${baseClasses} ${typeClasses} translate-y-full opacity-0`; // Start hidden below
    toast.textContent = message;

    toastContainer.prepend(toast); // Add new toasts to the top

    // Animate in
    requestAnimationFrame(() => {
        toast.classList.remove('translate-y-full', 'opacity-0');
        toast.classList.add('translate-y-0', 'opacity-100');
    });

    // Auto remove after delay
    setTimeout(() => {
        toast.classList.remove('translate-y-0', 'opacity-100');
        toast.classList.add('opacity-0'); // Fade out
        toast.addEventListener('transitionend', () => {
            toast.remove();
            if (!toastContainer.hasChildNodes()) {
                 // Optional: remove container if empty
                 // toastContainer.remove();
             }
        }, { once: true });
    }, 3000); // Keep toast for 3 seconds
}

function createToastContainer() {
    let container = document.getElementById('toast-container');
    if (!container) {
        container = document.createElement('div');
        container.id = 'toast-container';
        container.className = 'fixed bottom-4 right-4 z-50 w-full max-w-xs sm:max-w-sm'; // Position bottom-right
        document.body.appendChild(container);
    }
    return container;
}


// NOTE: WebSocket code removed for brevity as the focus shifted to polling/HTMX,
// but can be added back if real-time updates beyond polling are needed.
// function setupWebSocket() { ... }
// function updateUI(data) { ... }


// Add loading indicators (using HTMX events) - Optional visual flair
 htmx.on('htmx:beforeRequest', (event) => {
     const target = event.detail.target;
     // Apply loading opacity to the target container being updated
     if (target?.id && (target.id === 'players-container' || target.id === 'stats-container')) {
         target.classList.add('opacity-75', 'transition-opacity', 'duration-300');
     }
 });

 htmx.on('htmx:afterRequest', (event) => {
     const target = event.detail.target;
      if (target?.id && (target.id === 'players-container' || target.id === 'stats-container')) {
         target.classList.remove('opacity-75'); // Remove opacity after content is swapped
     }
 });
 
 function setupThemeToggle() {
    const toggleButton = document.getElementById('toggle-k-on-theme');
    const body = document.getElementById('app-body');

    if (toggleButton && body) {
        toggleButton.addEventListener('click', () => {
            body.classList.toggle('k-on-theme');
        });
    }
}