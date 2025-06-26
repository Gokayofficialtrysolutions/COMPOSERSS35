define([
    'base/js/namespace',
    'jquery',
    'require',
    requirejs.toUrl('./lib/lz-string.min.js'), // Local path
    requirejs.toUrl('./lib/qrcode.min.js')     // Local path
], function(
    jupyter, $, requirejs, LZString, QRCode // Ensure the variable names match what the libraries export
) {

    /** is app mode active */
    let appActive = false;

    /**
     * Handler to be called when a cell is selected. Just unselect it.
     * @function handleCellSelection
     */
    function handleCellSelection() {
        if(!appActive) { // disable
            return;
        }
        $(".app-view").removeClass("selected");
    }

    function goFullscreen() {
        document.documentElement.requestFullscreen().then(_ => {
            console.log("Fullscreen started");
        }, error => {
            console.log("Fullscreen rejected");
        });
    }

    /**
     * Activate the app mode, build viewId index and initialize event listeners
     * @function activateApp
     */
    function activateApp() {
        appActive = true;
        // add class to body to make CSS rules apply
        $("body").addClass("app-mode");

        // add class to only show favorite gates per default
        $("body").addClass("show-fav-gates")

        //
        // loop cells, get their viewIds and add corresponding classes
        //
        // keep track of very first view (default)
        jupyter.notebook.get_cells().map((cell, idx) => {
            const cellContent = cell.get_text();
            // if it is a view cell
            if(cellContent.startsWith("### APP")) {
                // add CSS classes to cells
                $(cell.element).addClass("app-view");
            }
        });
        // disable selection of cells
        $(jupyter.events).on("select.Cell", handleCellSelection);

        goFullscreen();

        // automatically restart
        restart();
    }

    /**
     * Deactivate the app mode, remove event listeners
     * @function deactivateApp
     */
    function deactivateApp() {
        appActive = false;
        // remove class from body
        $("body").removeClass("app-mode");
        // enable selection of cells
        $(jupyter.events).off("select.Cell", handleCellSelection);
    }

    /**
     * Restart kernel, execute all cells and block view with an overlay during this time
     * @function restart
     */
    function restart() {
        // add an overlay
        $("body").prepend('<div id="restart-overlay"><h1>Reloading</h1></div>');
        // restart kernel and execute all cells
        jupyter.actions.call("jupyter-notebook:restart-kernel-and-run-all-cells");
        // periodically check when the notebook is ready
        setTimeout(() => {
            var restartInterval = setInterval(() => {
                if(!jupyter.notebook.kernel_busy) {
                    clearInterval(restartInterval);
                    $("#restart-overlay").remove(); // remove overlay
                }
            }, 1000)
        }, 1000)
    }

    /**
     * Toggle class on body "show-fav-gates". This toggles the CSS state of additional gates
     * @function toggleGates
     */
    function toggleGates() {
        $("body").toggleClass("show-fav-gates");
    }

    /**
     * Call backend to refresh authentication i.e. access tokens
     * @function refreshAuth
     */
    function refreshAuth() {
        console.log("Start refreshing auth key")

        function setAuthStatus(success) {
            const color = (success) ? 'green' : 'red';
            document.getElementById('refreshauth-button-container').style.backgroundColor = color;
            setTimeout(() => {
                document.getElementById('refreshauth-button-container').style.backgroundColor = null;
            }, 2000);
        }

        return new Promise((resolve, reject) => {
            // do POST request to Jupyter backend
            fetch("/auth/refresh", {
                method: 'get',
                credentials: 'same-origin',
                headers: {
                    'X-XSRFToken': document.cookie.replace("_xsrf=", "")
                }
            }).then(response => {
                // if fail, alert and go to welcome
                if(!response.ok) {
                    setAuthStatus(false);
                    alert("Authentication with Homeconnect failed.");
                    window.open('/auth', '_blank');
                    reject();
                }
                // if succeed to to success
                else {
                    setAuthStatus(true);
                    resolve();
                }
            }, error => {
                alert("Authentication with Homeconnect failed.");
                window.open('/auth', '_blank');
                console.error(error);
                reject(error);
            })
        })
    }

    /**
     * Call backend to activate the coffee machine i.e. to set the power state to on
     * @function activateCoffeeMachine
     */
    function activateCoffeeMachine() {
        console.log("Activating coffee machine")
        return new Promise((resolve, reject) => {
            // do POST request to Jupyter backend
            fetch("/machine/power", {
                method: 'post',
                credentials: 'same-origin',
                headers: {
                    'X-XSRFToken': document.cookie.replace("_xsrf=", "")
                }
            }).then(response => {
                if (response.status === 202) { // Queued
                    response.json().then(body => {
                        const msg = body.message || "Coffee machine activation command queued.";
                        alert(msg);
                        updateGlobalStatus(msg, 'info', 5000); // Show for 5 seconds
                        resolve({"status": "queued", "response": body});
                    }).catch(() => {
                        const msg = "Coffee machine activation command queued (could not parse server message).";
                        alert(msg);
                        updateGlobalStatus(msg, 'warning', 5000);
                        resolve({"status": "queued"});
                    });
                } else if (!response.ok) {
                    const errorMsg = "Could not activate coffee machine. Status: " + response.status;
                    alert(errorMsg);
                    updateGlobalStatus(errorMsg, 'error', 5000);
                    reject({"status": "error", "http_status": response.status});
                } else { // OK
                    console.log("Coffee machine activated (or command sent successfully).");
                    updateGlobalStatus("Machine activated!", 'info', 3000);
                    resolve({"status": "ok"});
                }
            }, error => {
                alert("Could not activate coffee machine.");
                console.error(error);
                reject(error);
            })
        })
    }

    /**
     * Request a drink from the coffee machine
     * @function requestDrink
     * @param {string} drinkKey A valid programme for the coffee machine
     * @param {Object} drinkOptions A map of valid programm options with the corresponding values
     */
    function requestDrink(drinkKey, drinkOptions) {
        console.log("Start requesting", drinkKey, "with options", drinkOptions)
        return new Promise((resolve, reject) => {
            // tea is not supported by API
            if(drinkKey == "NotImplemented") {
                alert("Unfortunately, the Coffee Machine does not implement this beverage. Please start by hand.");
                resolve();
                return;
            }
            // do POST request to Jupyter backend
            fetch("/drink", {
                method: 'post',
                credentials: 'same-origin',
                headers: {
                    'X-XSRFToken': document.cookie.replace("_xsrf=", "")
                },
                body: JSON.stringify({
                    key: drinkKey,
                    options: drinkOptions
                })
            }).then(response => {
                if (response.status === 202) { // Queued
                    return response.json().then(body => {
                        const msg = body.message || "Drink command queued.";
                        alert(msg);
                        updateGlobalStatus(msg, 'info', 5000);
                        // Resolve with a structure that Python response_handler can use
                        resolve({ "status": "queued", "message": body.message, "details": body.details });
                    }).catch(() => {
                        const msg = "Drink command queued (could not parse server message).";
                        alert(msg);
                        updateGlobalStatus(msg, 'warning', 5000);
                        resolve({ "status": "queued", "message": "Drink command queued (server message parse error)." });
                    });
                } else if (!response.ok) {
                    // Try to get error message from backend if available
                    return response.text().then(text => { // Use text() first as it might not be JSON
                        let errorMsgDisplayed = "Could not get drink.";
                        try {
                            const errorBody = JSON.parse(text);
                            errorMsgDisplayed = "Could not get drink: " + (errorBody.error || errorBody.message || response.statusText);
                            alert(errorMsgDisplayed);
                            reject({ "status": "error", "http_status": response.status, "message": (errorBody.error || errorBody.message || response.statusText), "body": errorBody });
                        } catch (e) {
                            errorMsgDisplayed = "Could not get drink. Status: " + response.status + ". " + text;
                            alert(errorMsgDisplayed);
                            reject({ "status": "error", "http_status": response.status, "message": text });
                        }
                        updateGlobalStatus(errorMsgDisplayed, 'error', 5000);
                    });
                } else { // OK (live success)
                    const successMsg = "Drink command sent successfully!";
                    console.log(successMsg);
                    updateGlobalStatus(successMsg, 'info', 3000);
                    // Resolve with a structure that Python response_handler can use
                    resolve({ "status": "ok" });
                }
            }, error => {
                reject(error);
                alert("Could not get drink\n"+response.statusText);
                console.error(error);
            })
        })
    }

    /**
     * Close fullscreen
     * @function closeFullscreen
     */
    function closeFullscreen() {
        // close full screen if activated
        try {
            const exitFullscreenFn = document.exitFullscreen
            || document.webkitExitFullscreen
            || document.mozCancelFullScreen
            || document.msExitFullscreen
            exitFullscreenFn.call(document);
        } catch (error) {
            console.info("Not able to close fullscreen, fail silently")
        }
        return true;
    }

    /**
     * Open Help Overlay
     * @function openHelp
     */
    function openHelp() {
        // clear previous qr code
        $("#qrcode-container").empty();
        $("#qrcode-container").append(`
            <a class="help-link" target="_blank" onclick="window.myCloseFullscreen()" href="http://qoffee-maker.org">Qoffee Maker<br/><i>http://qoffee-maker.org</i><span class="arrow">→</span><a/>
            <a class="help-link" target="_blank" onclick="window.myCloseFullscreen()" href="http://quantum-computing.ibm.com">IBM Quantum<br/><i>http://quantum-computing.ibm.com</i><span class="arrow">→</span><a/>
            <p style="font-size: 0.8em; margin-top: 15px; text-align: center;"><i>Note: Accessing these links requires an internet connection.</i></p>
        `)
        $("#qrcode-container").addClass("active");
    }

    /**
     * Open an overlay which displays a QR Code
     * @function openQRCode
     * @param {string} url URL to encode into a QR Code
     * @param {string} text Text to show above the QR Code
     * @param {string} additionalHtml Optional HTML content to append below the QR code and link
     */
    function openQRCode(url, text="", additionalHtml="") {
        // clear previous qr code
        const qrContainer = $("#qrcode-container");
        qrContainer.empty();
        qrContainer.append('<div id="qrcode"></div>'); // Add div for QRCode object

        // create qrcode
        new QRCode(document.getElementById("qrcode"), { // QRCode is now correctly capitalized
            text: url,
            width: 256,
            height: 256,
            colorDark : "#000000",
            colorLight : "#ffffff"
        });

        if(text) { // Check if text is not empty or undefined
            qrContainer.prepend('<p class="qrcode-text">'+text+'</p>');
        }
        qrContainer.append('<a class="qrcode-link" href="'+url+'" target="_blank" rel="noopener noreferrer">Open Link</a>');

        if (additionalHtml) {
            qrContainer.append(additionalHtml);
        }
        qrContainer.addClass("active");
    }

    /**
     * Export a circuit to IBM Quantum Composer using URL
     * @function openQRCodeIBMQ
     * @param {string} circuitQasm QASM Code of the current circuit
     */
    function openQRCodeIBMQ(circuitQasm) {
        // setup data to transfer
        const dataToCompress = { // Renamed to avoid conflict with global 'data' widget if any confusion
            title: 'Qoffee Maker - ' +(new Date()).toLocaleString(),
            description: 'Circuit exported from Qoffee Maker',
            qasm: circuitQasm
        }
        // encode data and add to URL
        const quantumComposerComponent = encodeURIComponent(LZString.compressToEncodedURIComponent(JSON.stringify(dataToCompress)));
        const url = "https://quantum-computing.ibm.com/composer/files/new?initial="+quantumComposerComponent;

        // Prepare message for the QR code display
        let messageText = "Scan to open in IBM Quantum Composer.";
        // TODO: Check actual overall online status if possible. For now, assume it might be offline.
        messageText += "<br><small><i>Note: Accessing IBM Quantum Composer requires an internet connection.</i></small>";

        // Display QASM as text for copying, and a placeholder for where it could go in UI
        const qasmDisplayHtml = `<div style="margin-top: 10px;">
            <p><strong>Raw QASM:</strong></p>
            <textarea rows="5" style="width: 100%; font-family: monospace; font-size: 0.8em;" readonly>${circuitQasm}</textarea>
            <p><small>You can copy the QASM above if offline.</small></p>
            </div>`;

        console.log("QASM for IBM Quantum Composer:", circuitQasm); // For debugging / manual copy

        // show QR Code
        openQRCode(url, messageText, qasmDisplayHtml); // Pass additional HTML to display
    }

    //
    // Ipython Extension code
    //

    // state variable to avoid double loading
    let loadFunctionCalled = false;
    // interval for refreshing auth
    let intervalAuthRefresh = null;
    function load_ipython_extension() {
        // avoid double loading
        if(loadFunctionCalled) {
            return;
        }
        loadFunctionCalled = true;

        // load CSS file
        $('<link/>').attr({
            id: 'app_css',
            rel: 'stylesheet',
            type: 'text/css',
            href: requirejs.toUrl('./app.css')
        }).appendTo('head');

        // add button to toolbar to start app mode
        jupyter.toolbar.add_buttons_group([
            jupyter.actions.register({
                icon: 'fa-rocket',
                help: 'Activate App Mode',
                handler : activateApp
            }, 'app-activate', 'simple-app')
        ]);

        // add keyboard shortcut to leave app mode
        jupyter.actions.register({
            icon: 'fa-times',
            help: 'Deactivate App Mode',
            handler : deactivateApp
        }, 'app-deactivate', 'simple-app');
        jupyter.keyboard_manager.command_shortcuts.add_shortcut('esc', 'simple-app:app-deactivate');

        // publish methods by putting them onto window
        window.requestDrink = requestDrink
        window.openQRCodeIBMQ = openQRCodeIBMQ
        window.openQRCode = openQRCode
        window.openHelp = openHelp
        window.myCloseFullscreen = closeFullscreen
        window.refreshAuth = refreshAuth
        window.toggleGates = toggleGates
        window.activateCoffeeMachine = activateCoffeeMachine

        // set interval to refresh auth token
        clearInterval(intervalAuthRefresh)
        intervalAuthRefresh = setInterval(() => {
            refreshAuth();
        }, 40*60*1000)  // every 40min

        // add a button to UI which restarts the app
        $("body").append('<div id="restart-button-container" class="emergency-button-container"><button type="button" id="restart-button">Restart</button></div>')
        $(document).on("click", "#restart-button", restart);

        // add a button to UI which refreshs auth manually
        $("body").append('<div id="refreshauth-button-container" class="emergency-button-container"><button type="button" id="refreshauth-button">Refresh Auth</button></div>')
        $(document).on("click", "#refreshauth-button", refreshAuth);

        // add a button to UI to go fullscreen
        $("body").append('<div id="fullscreen-button-container" class="emergency-button-container"><button type="button" id="fullscreen-button">Fullscreen</button></div>')
        $(document).on("click", "#fullscreen-button", goFullscreen);

        /*
            Add QR Code Container
        */
        // add container to render QRCode
        $('body').append('<div id="qrcode-container"></div>');
        // add listener to close on click
        $("#qrcode-container").on("click", "*", event => {
            $("#qrcode-container").removeClass("active");
        })
        $("#qrcode-container").on("click", event => {
            $("#qrcode-container").removeClass("active");
        });

        // Add a global status bar
        $('body').append('<div id="qoffee-global-status-bar" style="position: fixed; bottom: 0; left: 0; width: 100%; background-color: #333; color: white; padding: 5px 10px; font-size: 0.9em; z-index: 10000; text-align: center; display: none;">Qoffee Status</div>');
        // Initial online status check for the bar
        updateOnlineStatus();
        // Start polling for queue status
        startQueueStatusPolling();
    }

    // Helper function to update the global status bar
    function updateGlobalStatus(message, type = 'info', duration = 0) {
        const statusBar = $('#qoffee-global-status-bar');
        if (!statusBar.length) return;

        statusBar.text(message).show();
        statusBar.css('background-color', type === 'error' ? '#c00' : type === 'warning' ? '#f0ad4e' : '#337ab7'); // Simple color coding

        if (duration > 0) {
            setTimeout(() => {
                statusBar.hide();
            }, duration);
        }
        // If duration is 0, message stays until changed or hidden explicitly
    }
    // Expose to window if needed by other parts or for debugging, otherwise keep local.
    window.updateQoffeeGlobalStatus = updateGlobalStatus; // Exposing for potential external calls or debug

    // Basic online/offline detection for the global status bar
    function updateOnlineStatus() {
        if (navigator.onLine) {
            updateGlobalStatus("Network: Online", 'info', 4000);
        } else {
            updateGlobalStatus("Network: Offline", 'warning'); // Keep offline message visible
        }
    }

    window.addEventListener('online', updateOnlineStatus);
    window.addEventListener('offline', updateOnlineStatus);
    // Initial check
    // updateOnlineStatus(); // Called now in load_ipython_extension

    // --- Global Status Bar & Queue Polling ---
    // The qoffee-global-status-bar provides users with feedback on network status,
    // queued commands, and other important application states.
    // It's updated by direct calls to updateGlobalStatus() or via the queue status poller.

    let queueStatusPollerInterval = null; // Interval ID for the poller
    const POLLING_INTERVAL = 30000; // Poll for queue status every 30 seconds

    /**
     * Fetches the Home Connect queue status from the backend API
     * and updates the global status bar accordingly.
     * Only polls if navigator.onLine is true.
     */
    function fetchAndUpdateQueueStatus() {
        if (!navigator.onLine) {
            // If browser thinks it's offline, no point in polling our backend for this.
            // The generic 'Network: Offline' message from updateOnlineStatus() should cover it.
            // Or, we could set a specific "Queue status: Offline / Unknown"
            // updateGlobalStatus("Queue status: Offline / Unknown", 'warning');
            return;
        }

        fetch("/api/hc/queue-status", {
            method: 'get',
            credentials: 'same-origin',
            headers: { 'X-XSRFToken': document.cookie.replace("_xsrf=", "") }
        })
        .then(response => {
            if (response.ok) {
                return response.json();
            }
            // Don't show error for failed poll, just log it, to avoid annoying user.
            console.error("Failed to fetch queue status:", response.status);
            return null;
        })
        .then(data => {
            if (data) {
                let statusMsg = `Network: Online`;
                if (data.active_queue_length > 0) {
                    statusMsg += ` | Queued: ${data.active_queue_length}`;
                }
                if (data.failed_queue_length > 0) {
                    statusMsg += ` | Failed: ${data.failed_queue_length}`;
                    updateGlobalStatus(statusMsg, 'warning'); // Keep visible if there are failed items
                } else if (data.active_queue_length > 0) {
                    updateGlobalStatus(statusMsg, 'info'); // Keep visible if items are queued
                } else {
                    // If everything is fine, show briefly or not at all,
                    // or integrate with the 'Network: Online' message from updateOnlineStatus
                    // For now, let updateOnlineStatus handle the pure "Online" message.
                    // This function will only make the bar persistent if there's something in queues.
                }
            }
        })
        .catch(error => {
            console.error("Error fetching or processing queue status:", error);
            // updateGlobalStatus("Could not fetch queue status.", 'error', 5000);
        });
    }

    function startQueueStatusPolling() {
        if (queueStatusPollerInterval) {
            clearInterval(queueStatusPollerInterval);
        }
        fetchAndUpdateQueueStatus(); // Initial fetch
        queueStatusPollerInterval = setInterval(fetchAndUpdateQueueStatus, POLLING_INTERVAL);
        console.log("Queue status polling started.");
    }

    function stopQueueStatusPolling() {
        if (queueStatusPollerInterval) {
            clearInterval(queueStatusPollerInterval);
            queueStatusPollerInterval = null;
            console.log("Queue status polling stopped.");
        }
    }
    // Expose for potential manual start/stop or if other logic needs to control it
    // window.startQoffeeQueuePolling = startQueueStatusPolling;
    // window.stopQoffeeQueuePolling = stopQueueStatusPolling;


    return {
        load_ipython_extension: load_ipython_extension
    };
});