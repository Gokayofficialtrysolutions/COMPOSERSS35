# CHIMera Explorer Frontend (`qoffeefrontend` directory)

**Note:** This documentation is being updated. With the project's pivot to the "CHIMera Explorer" (an offline Quantum Combinatorics tool), parts of this frontend's functionality, especially those related to Home Connect, are now considered legacy or less central. The core `app.js` and `app.css` still provide essential UI shell features for `chimera.ipynb`. The `qoffeefrontend` directory name is preserved due to tool limitations during renaming.

This is a Jupyter Notebook Extension which bundles JavaScript functions (`app.js`) and CSS Code (`app.css`) required for the CHIMera Explorer application's frontend interactivity and appearance within the Jupyter Notebook.

For overall project setup, architecture, and manual UI configuration in `chimera.ipynb`, please refer to the main project [README.md](../README.md) and the [DEVELOPER_GUIDE.md](../DEVELOPER_GUIDE.md).

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
- (Legacy) Counts of currently queued Home Connect commands and persistently failed commands (polled from `/api/hc/queue-status`). This part is less relevant for the CHIMera Explorer's core offline focus.
- Temporary messages for actions.

## Coffee Machine Interaction & Offline Support (Legacy Features)

The following JavaScript functions interface with the backend `qoffeeapi` for Home Connect operations. These are preserved from the original project but are considered legacy for the CHIMera Explorer.

### Refreshing Authorization to HomeConnect API 

- **`window.refreshAuth()`**: Manually refreshes the Home Connect API access token.

### Activate Coffee Machine

- **`window.activateCoffeeMachine()`**: Sends a command to turn the coffee machine on.

### Request a drink from the Coffee Machine

- **`window.requestDrink(<programm key>, <map of programm options>)`**: Sends a command to make a drink.

## Help Display

- **`window.openHelp()`**: Displays links to external project and IBM Quantum pages. The UI now includes a note that accessing these links requires an internet connection.