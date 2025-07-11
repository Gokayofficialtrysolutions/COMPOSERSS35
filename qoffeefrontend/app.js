define([
    'base/js/namespace',
    'jquery',
    'require',
    requirejs.toUrl('./lib/lz-string.min.js'), // Local path for LZString
    requirejs.toUrl('./lib/qrcode.min.js')     // Local path for QRCode.js
], function(
    jupyter, $, requirejs, LZString, QRCode // Arguments for loaded modules
) {

    /** is app mode active */
    let appActive = false;

    /**
     * Handler to be called when a cell is selected. Just unselect it in app mode.
     */
    function handleCellSelection() {
        if(!appActive) {
            return;
        }
        // Assuming ".app-view" is a class you might add to cells part of your app's UI
        // to differentiate them, or this might need adjustment based on how views are defined.
        // For now, it just ensures no cells can be selected in app mode.
        jupyter.notebook.getSelectedCells().forEach(cell => cell.unselect());
        // Alternative: $(".selected").removeClass("selected"); if cells get 'selected' class
    }

    /**
     * Attempts to request fullscreen mode for the document.
     */
    function goFullscreen() {
        if (document.documentElement.requestFullscreen) {
            document.documentElement.requestFullscreen().then(() => {
                console.log("Fullscreen activated.");
            }).catch(err => {
                console.log(`Fullscreen request failed: ${err.message} (${err.name})`);
            });
        } else {
            console.log("Fullscreen API not supported by this browser.");
        }
    }

    /**
     * Activates the application mode: hides Jupyter UI elements, enables app-specific CSS.
     */
    function activateApp() {
        appActive = true;
        $("body").addClass("app-mode show-fav-gates"); // Combine classes

        // Example: Add CSS classes to cells intended as app views (if any)
        // This part might be less relevant if the entire notebook IS the app view.
        jupyter.notebook.get_cells().forEach(cell => {
            const cellContent = cell.get_text();
            if(cellContent.startsWith("### APP_VIEW_IDENTIFIER")) { // Example identifier
                $(cell.element).addClass("chimera-app-cell-view"); // CHIMera
            }
        });

        // Prevent cell selection in app mode
        $(jupyter.events).on("select.Cell", handleCellSelection);

        // Optional: Attempt fullscreen
        // goFullscreen(); // Commented out as it can be intrusive

        // Optional: Restart kernel and run all (if this is desired app startup behavior)
        // restartKernelAndRunAll();
        console.log("CHIMera Explorer App Mode Activated."); // CHIMera
    }

    /**
     * Deactivates the application mode: shows Jupyter UI elements, removes app-specific CSS.
     */
    function deactivateApp() {
        appActive = false;
        $("body").removeClass("app-mode show-fav-gates");
        $(jupyter.events).off("select.Cell", handleCellSelection);

        // Optional: Exit fullscreen if it was entered
        // if (document.fullscreenElement) {
        //     document.exitFullscreen();
        // }
        console.log("CHIMera Explorer App Mode Deactivated."); // CHIMera
    }

    /**
     * Restarts the Jupyter kernel and runs all cells. Shows a loading overlay.
     * This is a powerful action and should be used judiciously.
     */
    function restartKernelAndRunAll() {
        $("body").prepend('<div id="chimera-restart-overlay" style="position:fixed; top:0;left:0;width:100%;height:100%;background:rgba(0,0,0,0.7);color:white;z-index:20000;display:flex;align-items:center;justify-content:center;"><h1>Reloading Application & Kernel...</h1></div>'); // CHIMera
        jupyter.actions.call("jupyter-notebook:restart-kernel-and-run-all-cells");

        // Periodically check for kernel busy state to remove overlay
        let restartCheckInterval = setInterval(() => {
            if (jupyter.notebook && !jupyter.notebook.kernel_busy) {
                clearInterval(restartCheckInterval);
                $("#chimera-restart-overlay").remove(); // CHIMera
                console.log("Kernel restarted and cells run.");
            }
        }, 1000);
    }

    /**
     * Toggles visibility of less frequently used quantum gates in the composer.
     * Relies on CSS class `show-fav-gates` on `body`.
     */
    function toggleGates() {
        $("body").toggleClass("show-fav-gates");
    }

    /**
     * Closes fullscreen mode if active.
     */
    function closeFullscreen() {
        if (document.fullscreenElement) {
            document.exitFullscreen().catch(err => console.info("Could not exit fullscreen:", err));
        }
        return true;
    }

    /**
     * Opens the Help/Information Overlay.
     * Displays links to external project documentation and IBM Quantum resources.
     */
    function openHelp() {
        const qrContainer = $("#qrcode-container"); // Assumes this div is still used/created for overlays
        qrContainer.empty(); // Clear previous content
        qrContainer.append(`
            <div style="padding:20px; text-align:center;">
                <h3>CHIMera Explorer - Help & Resources</h3>
                <p><a class="help-link" target="_blank" rel="noopener noreferrer" href="http://qoffee-maker.org">CHIMera Explorer Project Page (Link needs update if changed)</a></p>
                <p><a class="help-link" target="_blank" rel="noopener noreferrer" href="https://quantum-computing.ibm.com">IBM Quantum Platform</a></p>
                <p style="font-size: 0.8em; margin-top: 15px;"><i>Note: Accessing these links requires an internet connection.</i></p>
                <button onclick="$('#qrcode-container').removeClass('active');" style="margin-top:15px;">Close</button>
            </div>
        `);
        qrContainer.addClass("active"); // Show the overlay
    }

    /**
     * Opens an overlay displaying a QR Code for a given URL.
     * Also displays optional text and additional HTML content.
     */
    function openQRCode(url, text = "", additionalHtml = "") {
        const qrContainer = $("#qrcode-container");
        qrContainer.empty();
        qrContainer.append('<div id="qrcode-img" style="margin:20px auto; width:256px; height:256px;"></div>'); // Div for QRCode.js to target

        new QRCode(document.getElementById("qrcode-img"), {
            text: url,
            width: 256,
            height: 256,
            colorDark: "#000000",
            colorLight: "#ffffff",
            correctLevel: QRCode.CorrectLevel.H
        });

        if (text) {
            qrContainer.prepend('<p class="qrcode-text" style="text-align:center; margin:10px;">' + text + '</p>');
        }
        qrContainer.append('<p style="text-align:center; margin-top:10px;"><a class="qrcode-link" href="' + url + '" target="_blank" rel="noopener noreferrer">Open Link</a></p>');

        if (additionalHtml) {
            qrContainer.append('<div style="margin-top:10px; padding:0 20px; text-align:left;">' + additionalHtml + '</div>');
        }
        qrContainer.append('<button onclick="$(\'#qrcode-container\').removeClass(\'active\');" style="margin:15px auto; display:block;">Close</button>');
        qrContainer.addClass("active");
    }

    /**
     * Generates a QR code for exporting the current circuit QASM to IBM Quantum Composer.
     * This feature is for users who might want to take their circuit online.
     */
    function openQRCodeIBMQ(circuitQasm) {
        const dataToCompress = {
            title: 'CHIMera Explorer Circuit - ' + (new Date()).toLocaleString(), // CHIMera
            description: 'Circuit exported from CHIMera Explorer (Offline Quantum Combinatorics Tool)', // CHIMera
            qasm: circuitQasm
        };
        const quantumComposerComponent = encodeURIComponent(LZString.compressToEncodedURIComponent(JSON.stringify(dataToCompress)));
        const url = "https://quantum-computing.ibm.com/composer/files/new?initial=" + quantumComposerComponent;

        let messageText = "Scan to open in IBM Quantum Composer.";
        messageText += "<br><small><i>Note: Accessing IBM Quantum Composer requires an internet connection.</i></small>";

        const qasmDisplayHtml = `<div style="margin-top: 10px;">
            <p><strong>Raw QASM:</strong></p>
            <textarea rows="5" style="width: 100%; font-family: monospace; font-size: 0.8em; box-sizing: border-box;" readonly>${circuitQasm}</textarea>
            <p><small>You can copy the QASM above.</small></p>
            </div>`;

        openQRCode(url, messageText, qasmDisplayHtml);
    }

    // --- Global Status Bar ---
    // Provides simple, non-intrusive feedback at the bottom of the page.

    /**
     * Updates the global status bar message and appearance.
     * @param {string} message - The message to display.
     * @param {'info'|'warning'|'error'} type - Type of message for color coding.
     * @param {number} duration - How long to display (ms). 0 for persistent until next update.
     */
    function updateGlobalStatus(message, type = 'info', duration = 0) {
        const statusBar = $('#chimera-global-status-bar'); // CHIMera
        if (!statusBar.length) return;

        statusBar.text(message).show();
        let bgColor = '#337ab7'; // Default info blue
        if (type === 'error') bgColor = '#c00'; // Red
        if (type === 'warning') bgColor = '#f0ad4e'; // Orange
        statusBar.css('background-color', bgColor);

        if (duration > 0) {
            setTimeout(() => {
                statusBar.fadeOut();
            }, duration);
        }
    }
    window.updateCHIMeraGlobalStatus = updateGlobalStatus; // CHIMera - Expose for potential external calls or debug

    /**
     * Updates the global status bar based on browser's navigator.onLine status.
     * Note: navigator.onLine is not always a reliable indicator of actual internet connectivity.
     */
    function updateOnlineStatusDisplay() {
        if (navigator.onLine) {
            updateGlobalStatus("Network: Browser Online", 'info', 4000);
        } else {
            updateGlobalStatus("Network: Browser Offline", 'warning'); // Keep offline message visible
        }
    }

    // --- IPython Extension Setup ---
    let loadFunctionCalled = false;

    function load_ipython_extension() {
        if (loadFunctionCalled) {
            return;
        }
        loadFunctionCalled = true;

        // Load main application CSS
        $('<link/>').attr({
            id: 'chimera_app_css', // CHIMera
            rel: 'stylesheet',
            type: 'text/css',
            href: requirejs.toUrl('./app.css') // Assuming app.css is in the same dir
        }).appendTo('head');

        // App Mode Activation Button (Toolbar)
        if (jupyter && jupyter.toolbar) {
            jupyter.toolbar.add_buttons_group([
                jupyter.actions.register({
                    icon: 'fa-rocket', // FontAwesome icon
                    help: 'Activate CHIMera Explorer App Mode', // CHIMera
                    handler: activateApp
                }, 'chimera-app-activate', 'chimera-explorer') // CHIMera
            ]);
        }

        // Deactivate App Mode (Keyboard Shortcut: ESC)
        if (jupyter && jupyter.keyboard_manager) {
             jupyter.actions.register({
                icon: 'fa-times', // FontAwesome icon
                help: 'Deactivate CHIMera Explorer App Mode', // CHIMera
                handler: deactivateApp
            }, 'chimera-app-deactivate', 'chimera-explorer'); // CHIMera
            jupyter.keyboard_manager.command_shortcuts.add_shortcut('esc', 'chimera-explorer:chimera-app-deactivate'); // CHIMera
        }

        // Publish essential methods to window for Python (JsPyWidget) or HTML calls
        window.openQRCodeIBMQ = openQRCodeIBMQ;
        window.openQRCode = openQRCode; // General QR code utility
        window.openHelp = openHelp;
        window.myCloseFullscreen = closeFullscreen; // Retained if used by existing HTML
        window.toggleGates = toggleGates; // If gate set toggling is still desired
        // Removed: window.requestDrink, window.refreshAuth, window.activateCoffeeMachine

        // Emergency Restart Button (useful if UI becomes unresponsive)
        $("body").append('<div id="chimera-restart-button-container" style="position:fixed; bottom:30px; right:10px; z-index:20001;"><button type="button" id="chimera-restart-button" title="Restart Kernel & Run All">Restart App</button></div>'); // CHIMera
        $(document).on("click", "#chimera-restart-button", restartKernelAndRunAll); // CHIMera

        // Fullscreen Button (optional convenience)
        $("body").append('<div id="chimera-fullscreen-button-container" style="position:fixed; bottom:60px; right:10px; z-index:20001;"><button type="button" id="chimera-fullscreen-button" title="Toggle Fullscreen">Fullscreen</button></div>'); // CHIMera
        $(document).on("click", "#chimera-fullscreen-button", goFullscreen); // CHIMera


        // QR Code overlay container (shared by openQRCode and openHelp)
        // ID "qrcode-container" is generic enough, can be kept.
        $('body').append('<div id="qrcode-container" style="display:none; position:fixed; top:0;left:0;width:100%;height:100%;background:rgba(0,0,0,0.85);z-index:19999;color:white;overflow-y:auto;"></div>');
        $("#qrcode-container").on("click", function(event) { // Close overlay if background is clicked
            if (event.target === this) {
                $(this).removeClass("active").hide();
            }
        });
         // Ensure buttons inside also can close it, e.g., by adding a common class to close buttons
         // and $(document).on('click', '.close-qrcode-overlay', () => $('#qrcode-container').removeClass('active').hide());

        // Global Status Bar
        $('body').append('<div id="chimera-global-status-bar" style="position: fixed; bottom: 0; left: 0; width: 100%; background-color: #333; color: white; padding: 5px 10px; font-size: 0.9em; z-index: 10000; text-align: center; display: none;">CHIMera Explorer Status</div>'); // CHIMera

        // Initial network status display and event listeners
        window.addEventListener('online', updateOnlineStatusDisplay);
        window.addEventListener('offline', updateOnlineStatusDisplay);
        updateOnlineStatusDisplay(); // Initial check

        console.log("CHIMera Explorer frontend extension loaded."); // CHIMera
    }

    return {
        load_ipython_extension: load_ipython_extension
    };
});