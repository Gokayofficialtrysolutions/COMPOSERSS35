# Qoffeefrontend

This is a Jupyter Notebook Extension which bundles JavaScript functions and CSS Code required for the Qoffee functionality and app experience.

## App Mode

The extension enables an application mode. In this mode everything is hidden except for the output of code cells marked with `### APP`. This allows you to build hide all Jupyter Notebook related stuff and to just show your application, e.g. using [AppBox from appwidgets package](../appwidgets/appwidgets/switchbox.py). The CSS code for this is located in [](app.css) and is loaded on startup.

To activate the application, click on the rocket in the toolbar (or programatically trigger the action `app-activate`). To deactivate the application mode, press ESC (or programatically trigger the action `app-deactivate`). To restart the application, press restart on the bottom right of the screen. This will restart the Jupyter Kernel and execute all cells.

## QR Codes

The frontend provides utilities for displaying QR codes:

- **`window.openQRCode(<url>, text="", additionalHtml="")`**: Displays a QR code for the given URL in an overlay.
    - An optional `text` can be shown above the QR code.
    - Optional `additionalHtml` can be appended below the QR code (e.g., for raw QASM display).
    - The `qrcode.min.js` library used for this is now bundled locally, so QR codes can be generated even when offline.

- **`window.openQRCodeIBMQ(<circuit qasm code>)`**: Specifically for exporting circuits to IBM Quantum Composer.
    - It compresses the QASM (using the locally bundled `lz-string.min.js`) and constructs the URL.
    - The QR code overlay will include a note that accessing the IBM Quantum Composer website requires an internet connection.
    - It also displays the raw QASM text in a textarea for easy copying if offline.

## Global Status Bar

A global status bar is added at the bottom of the screen. It provides:
- Basic browser online/offline network status indication (via `navigator.onLine`).
- Counts of currently queued Home Connect commands and persistently failed commands (polled from `/api/hc/queue-status`).
- Temporary messages for actions like commands being queued or successfully sent.

## Coffee Machine Interaction & Offline Support

JavaScript functions interface with the backend `qoffeeapi` for Home Connect operations. These now support offline capabilities:

### Refreshing Authorization to HomeConnect API 

- **`window.refreshAuth()`**: Manually refreshes the Home Connect API access token. This requires an online connection. If authentication fails, it redirects to the login page. The button for this is on the bottom right.

### Activate Coffee Machine

- **`window.activateCoffeeMachine()`**: Sends a command to turn the coffee machine on.
    - If online, the command is sent directly.
    - If offline, the command is queued by the backend. A JavaScript `alert()` and a message in the global status bar will notify the user.

### Request a drink from the Coffee Machine

- **`window.requestDrink(<programm key>, <map of programm options>)`**: Sends a command to make a drink.
    - If online, the command is sent directly.
    - If offline, the command is queued. A JavaScript `alert()` and a message in the global status bar will notify the user.
    - The Python callback for this function receives a status indicating if the command was 'ok' (live) or 'queued'.

## Help Display

- **`window.openHelp()`**: Displays links to external project and IBM Quantum pages. The UI now includes a note that accessing these links requires an internet connection.