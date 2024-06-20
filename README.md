## Prerequisites

Before you begin, ensure you have met the following requirements:

- Python 3.6 or higher


## Installation

1. Clone the repository:

    ```bash
    git clone https://github.com/yourusername/BetCraft.git
    cd Bet-bot
    ```

2. Create and activate a virtual environment:

    ```bash
    python3 -m venv venv
    source venv/bin/activate  # On Windows use `venv\Scripts\activate`
    ```

3. Install the required dependencies:

    ```bash
    pip install -r requirements.txt
    ```


### Configuration

- **Telegram Bot API Key**: Create a new bot on Telegram by talking to [@BotFather](https://telegram.me/botfather) and following the instructions to get your bot API key.
- **BlockCypher API Key**: Sign up at [BlockCypher](https://www.blockcypher.com) and create an API token.
- **Coinbase Commerce API Key**: Sign up at [Coinbase Commerce](https://commerce.coinbase.com), create an API key in the settings.
- **The Odds API Key**: Sign up at [The Odds API](https://the-odds-api.com) and get your API key from the dashboard.
- **BetsAPI Key**: Sign up at [BetsAPI](https://betsapi.com) and obtain your API key from the user dashboard.
- **Firebase API Key**: Sign up at [Firebase](https://firebase.google.com), create a project, and obtain your Firebase credentials file. Update the `firebase_keys_path` in your `config.json` to point to the location of your `FireBaseKeys.json` file.

## Usage

1. Ensure your configuration file is correctly set up.
2. Run the bot:

    ```bash
    python main.py
    ```

3. Interact with the bot on Telegram using the username provided in the configuration.

## Bot Functionalities

### User Registration and Management

- **Registration**: New users can register with the bot by providing their details.
- **Profile Management**: Users can update their profile information, including their wallet addresses for deposits and withdrawals.

### Betting

- **Place Bets**: Users can place bets on various sports events using commands.
- **Bet History**: Users can view their betting history and track their performance.

### Financial Transactions

- **Deposits**: Users can deposit funds into their account via supported cryptocurrencies.
- **Withdrawals**: Users can request withdrawals, which will be processed with a small fee.
- **Fees**: Configurable deposit and withdrawal fees are applied to transactions.

### Admin Panel

- **User Management**: Admins can view and manage user accounts.
- **Bet Management**: Admins can oversee bets placed, approve or reject them as necessary.
- **Configuration**: Admins can update bot settings and configurations.

### Notifications and Alerts

- **Event Updates**: Users receive updates on sports events, including odds and results.
- **Transaction Alerts**: Users are notified of successful deposits, withdrawals, and bet outcomes.

### Security and Verification

- **Secure Transactions**: The bot uses API keys for secure transactions with external services.
- **Admin Approvals**: Certain actions, such as withdrawals, require admin approval to ensure security.

---

Feel free to reach out for support by contacting [@PublicVoiddev](https://t.me/Public_Void_dev) on Telegram.

