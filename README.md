# Qoffee-Maker

<img src="css/QoffeeMug.png">

## User Instructions

Find user instructions on the project GitHub pages: http://qoffee-maker.org

## Installation

As an example, we will install the Qoffee Maker Graphical User Interface (GUI) to be accessed under `https://localhost:8887`. It is also possible to choose another URL that you want to access the GUI from.
### Prerequisites

- Home Connect enabled coffee machine
- Android Phone or iPhone
- Computer
- Email address you will use to register with Home Connect


### Install Home Connect
1. Install the Home Connect [iOS App](https://app.adjust.com/gdi5c03?campaign=germany&redirect_macos=https%3A%2F%2Fapps.apple.com%2Fde%2Fapp%2Fhome-connect-app%2Fid901397789&redirect_windows=https%3A%2F%2Fapps.apple.com%2Fde%2Fapp%2Fhome-connect-app%2Fid901397789) or [Android App](https://app.adjust.com/gdi5c03?campaign=germany&redirect_macos=https%3A%2F%2Fplay.google.com%2Fstore%2Fapps%2Fdetails%3Fid%3Dcom.bshg.homeconnect.android.release%26hl%3Dde&redirect_windows=https%3A%2F%2Fplay.google.com%2Fstore%2Fapps%2Fdetails%3Fid%3Dcom.bshg.homeconnect.android.release%26hl%3Dde)

2. In the App Connect mobile app, you need to sign in with a Home Connect User Account.

After starting the app, the welcome screen will show the option to log in to the app or register a new user.

If you have not used the "Home Connect" app before follow these steps on how to create an account:

- Click on the Register link as shown in the picture below.

<p align="center">
<img src="css/HomeConnect_app_home_screen.png" width="300">
</p>

- Use your email address to register new user. Provide a new password as requested on the form:

<p align="center">
<img src="css/HomeConnect_app_user_registration.png" width="300">
</p>

- Then, press "Continue" link on the top-right corner.

- Read "Terms and Condition" rules, and accept it by checking "I have read and accept the terms of use" checkbox, then press "Continue" button.

- Once again, read "Data protection statement" and accept it by checking "I have read and accept the data protection statement" checkbox. Press "Continue" button to proceed.

- Read the statements regarding collecting user data and accept it by clicking "I consent to the collection of mu user data" checkbox. Press "Continue" button to finish procedure.

- Review the provided information and click "Send" button.

- Now, you have to activate the registered account. To confirm the account you must click the link in the activation email that you will receive in your mailbox.

- Now, you confirm your email address, your account will be activated and you can log in to the Home Connect app using your newly registered user.

3. Add your Coffee Machine appliance to the Home Connect App

You can connect your Coffee Machine under _Appliances_ in the App.

4. [Sign up for a Home Connect Developer Account](https://developer.home-connect.com/user/register)

Make sure to set your _Default Home Connect User Account for Testing_ to the Home Connect User Account (mail address) used in the previous step.

Hint: It is not crucial to provide meaningful _Additional Information_.

5. [Register a new Home Connect Appliance](https://developer.home-connect.com/applications/add)

Set an _Application ID_ of your choice. Using localhost, the _Redirect URI_ is set to `http://localhost:8887/auth/callback`. Keep the default settings for the remaining boxes and create the appliance.

### Install the Qoffee Maker GUI
Install the Qoffee Maker GUI by following these steps:

1. **Set up Environment Variables:**
   Copy the `env-template` file to a new file named `.env` in the root of the project:
   ```bash
   cp env-template .env
   ```
   Then, edit the `.env` file and fill in your specific values for the following variables:
    - `HOMECONNECT_API_URL`: Use `https://api.home-connect.com/` for a real device or `https://simulator.home-connect.com/` for the simulator.
    - `HOMECONNECT_CLIENT_ID`: Your Client ID from your registered Home Connect application.
    - `HOMECONNECT_CLIENT_SECRET`: Your Client Secret from your registered Home Connect application.
    - `HOMECONNECT_REDIRECT_URL`: Callback URL for HomeConnect as registered in your application in HomeConnect. On localhost this is `http://localhost:8887/auth/callback` (the port is determined by Jupyter, `/auth/callback` is fixed)
    - `DEVICE_HA_ID`: This is the HomeConnect Appliance ID (HA ID) of your coffee machine. It is useful when you have multiple coffee machines registered in your Home Connect App. Leave it blank if you don't want to set it/don't know about it.
      - To get the HA IDs of your available machines start the QoffeeMaker, authenticate and then, type http://{YOUR_IP_ADRESS}:8887/machines into your browser. You will get an response with all your appliances and HA IDs.
    - `IBMQ_API_KEY`: the API Key for [IBM Quantum](https://quantum-computing.ibm.com/account)

2. Run the container image with the specified environment variables: `docker run --name qoffee --rm -itp 8887:8887 --env-file .env ghcr.io/janlahmann/qoffee-maker`

3. Now you can start using the Qoffee Maker GUI under http://localhost:8887 (the login token is shown in the StdOut of the docker container). After logging in to Jupyter, you have to select _qoffee.ipynb_ and then you have to click the rocket icon to _Activate App Mode_.

Enjoy your Quantum Coffee. ☕️

## New Features & Capabilities

This version of Qoffee-Maker includes significant enhancements for offline operation and new educational features for exploring quantum concepts.

### Offline Capabilities

The Qoffee-Maker can now handle periods of internet disconnection more gracefully, particularly for Home Connect functionalities:

*   **Data Caching:** Information about your Home Connect appliances (list of machines, their status, and settings) is cached locally. If you are offline, the application will attempt to show you the most recently fetched data, indicating that it's cached and when it was last updated.
*   **Command Queuing:** If you try to perform actions like turning on your coffee machine or requesting a drink while offline, these commands will be automatically queued.
*   **Automatic Processing:** When an internet connection is restored, the application will attempt to process any queued commands.
*   **Retry Mechanism:** Queued commands that fail due to temporary issues (other than being offline) will be retried up to 3 times.
*   **Failed Commands:** Commands that persistently fail will be moved to a "failed commands queue."
    *   You can view the status of these queues via the API endpoint: `GET /api/hc/queue-status`.
    *   Failed commands can be managed (retried or deleted) via API endpoints:
        *   `POST /api/hc/retry-failed-command` (Body: `{"command_index": index}`)
        *   `POST /api/hc/delete-failed-command` (Body: `{"command_index": index}`)
    *   (Future UI enhancements may provide easier management of these queues).
*   **IBMQ Execution:** If you attempt to run a circuit on a real IBM Quantum device while offline, the system will automatically fall back to using a local noisy simulator. The "Export to IBM Quantum Composer" feature now bundles necessary libraries to generate QR codes offline, though accessing the IBM Quantum website itself still requires internet.
*   **Status Bar:** A global status bar at the bottom of the UI provides basic feedback on network status and queued/failed command counts.

### Combinatorial Quantum Circuits Feature

Explore fundamental quantum representations of combinatorial concepts:

*   **Binomial Distribution:** Generate circuits where qubit measurement probabilities follow a binomial distribution B(N, p).
    *   Examples: "Binomial (N=3, p=0.5)", "Binomial (N=4, p=0.25)"
*   **Permutations:**
    *   Simple examples like swapping qubit states (e.g., "2-Qubit SWAP(0,1)", "3-Qubit Cycle (0->1->2)").
    *   Generate circuits for custom permutations of basis states (e.g., "2Q Permutation ([0,2,1,3])").
*   **Combinations (N choose k):** Generate circuits that prepare an equal superposition of all basis states representing the selection of 'k' items from 'N'.
    *   Examples: "Combinations (N=3, k=2)", "Combinations (N=4, k=1)"

These features are best experienced by manually setting up the UI in `qoffee.ipynb`.
**Please refer to [MANUAL_QOFFEE_IPYNB_SETUP.md](MANUAL_QOFFEE_IPYNB_SETUP.md) for detailed step-by-step instructions.**

## Security Considerations

When setting up and running the Qoffee-Maker application, please be mindful of the following security aspects:

**1. API Credentials (`.env` file):**
   *   Your `.env` file will contain sensitive credentials:
        *   `HOMECONNECT_CLIENT_ID`
        *   `HOMECONNECT_CLIENT_SECRET`
        *   `IBMQ_API_KEY`
   *   **Action:** Protect your `.env` file as you would any file containing passwords or private keys. Do not commit it to public version control repositories. Ensure file permissions restrict access.
   *   The application loads these into environment variables. The `hc_connector.py` attempts to clear `HOMECONNECT_CLIENT_ID` and `HOMECONNECT_CLIENT_SECRET` from the environment after they are loaded by the connector instance, which is a good practice to reduce their exposure time in memory.

**2. Home Connect OAuth Tokens (`.user/oauth-token.json`):**
   *   This file stores your Home Connect OAuth access and refresh tokens, selected machine details, cached API responses, and queued commands.
   *   **Action:** This file is sensitive. It's stored in a dot-directory (`.user/`) which is typically hidden by default in file listings. Ensure the permissions on this file and directory restrict access appropriately.
   *   If this file is compromised, an attacker could potentially control your Home Connect appliances associated with these tokens until the tokens expire or are revoked.

**3. SSL/TLS Verification (`verify=False`):**
   *   In `qoffeeapi/oauth2.py`, network requests to the Home Connect API (and for online status checks) are made with `verify=False`. This disables SSL/TLS certificate verification for those connections.
   *   **Implication:** This was done for consistency with original project code and to ease local development setups where custom CA certificates or proxies might interfere. However, in a production or untrusted network environment, `verify=False` makes the application vulnerable to Man-in-the-Middle (MitM) attacks, where an attacker could intercept and potentially modify traffic to the Home Connect API.
   *   **Recommendation for Advanced Users/Production:** If deploying in a less trusted environment, you should investigate setting `verify=True` and ensuring your Python environment's trust store includes the necessary CA certificates for the Home Connect API (e.g., by setting the `REQUESTS_CA_BUNDLE` environment variable or ensuring system CAs are up-to-date). This might require more complex setup.

**4. Jupyter Server Security:**
   *   The Qoffee-Maker application runs as a Jupyter Notebook server extension.
   *   **Action:** Secure your Jupyter server itself.
        *   Use a strong, unique token or password for accessing the Jupyter server.
        *   Avoid running the Jupyter server on a publicly accessible IP address unless you have properly configured authentication and ideally HTTPS.
        *   Be mindful of who has access to the machine running the Jupyter server.
   *   Refer to the official [Jupyter Server security documentation](https://jupyter-server.readthedocs.io/en/latest/operators/security.html) for best practices.

**5. API Endpoint Exposure:**
   *   The custom API endpoints (e.g., `/auth`, `/drink`, `/api/hc/*`) are protected by Jupyter's `@web.authenticated` decorator, meaning a user must be logged into the Jupyter server to access them. This is a good baseline. The `/api/health` endpoint is public by design for diagnostics.
   *   No additional application-level authorization is implemented beyond Jupyter's authentication (e.g., there's no multi-user distinction within Qoffee-Maker itself).

**6. Code Execution from UI (`data-rh-exec`):**
   *   The `ReactiveHtmlWidget` in `appwidgets` allows HTML templates (defined in `qoffee.ipynb`) to specify Python code snippets to be executed via the `data-rh-exec` attribute.
   *   **Implication:** The Python code embedded in the notebook's HTML templates has the full permissions of the Jupyter kernel.
   *   **Action:** Only run `qoffee.ipynb` notebooks from trusted sources. Be cautious if modifying these `data-rh-exec` snippets.

**7. Docker Container Security:**
   *   If running via the provided Docker image (or building your own):
        *   Ensure the base Docker image is from a trusted source and kept up-to-date.
        *   Be mindful of any ports exposed from the container to the host.
        *   The current setup passes environment variables via an `--env-file`, which is a standard Docker practice.

By being aware of these points, you can use the Qoffee-Maker more securely.

## Installation on RasQberry (draft):

Installation and startup of Qoffee-Maker has been fully integrated to the RasQberry automated setup. (Currently in branch "dev8", but will be merged to master soon.)

In rasqberry-config (started with `$ . ./RasQ-init.sh dev9`), use the following menu items in "D Quantum Demos" to run the locally build docker image or the image available on dockerhub: "QM Qoffee-Maker", "QMd Qoffee-Maker".

To trigger a rebuild, choose "A Advanced Config" -> "QMrb Qoffee-Maker rebuild".

To stop all qoffee containers, select "A Advanced Config" -> "QMst stop Qoffee-Maker".

The two versions of the demo can also be started using the "Qoffee Maker" desktop icons.

