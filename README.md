# Solana Copy Trade Bot

**Sol_copy_bot** is a Python-based bot designed to automate *copy trading* on the Solana blockchain. The bot listens for transactions made by a target wallet and attempts to replicate (copy) them using your own funded wallet in real time.

> ⚠️ **Important Safety Note:** Crypto trading bots that require private keys carry significant risk. Ensure you thoroughly review, audit, and test any code before using it with real funds.

---

## 🚀 Features

- 🪙 Automatically detect and mirror transactions from a target wallet on the Solana network
- 🔗 Built in Python using Solana APIs and RPC endpoints
- ⚙️ Simple configuration via environment variables or config file
- 📊 Basic logging to help monitor bot activity

---

## 📦 Prerequisites

Before running the bot locally, ensure you have:

- Python 3.10+ installed
- A funded Solana wallet (private key)
- Access to a Solana RPC endpoint (e.g., public or third-party)
- (Optional) Virtual environment support (recommended)

---

## 📥 Installation

1. **Clone the repo**

   ```bash
   git clone https://github.com/Jinex2012/sol_copy_bot.git
   cd sol_copy_bot

2. **Install dependencies**

   Use Pipenv:
   ```bash
   pipenv install
   pipenv shell
   ```

3. **Configure environment**

   Copy the example environment file and set values:

   ```bash
   cp .env.example .env
   # then open .env and fill relevant values
   ```

---

## ⚙️ Configuration

Your `.env` file should include (example):

```
SOL_RPC=https://api.mainnet-beta.solana.com
```

> ⚠️ **Never commit your private keys to version control.**

---

## 🏃‍♂️ Running the Bot

With your config set:

```bash
python bot_copy_trade.py
```

The bot will connect to your specified RPC and begin listening for matching transactions to replicate.

---

## 🧠 How It Works

1. Connects to a Solana RPC endpoint
2. Monitors confirmed transactions on the blockchain
3. Filters for transactions originating from a *target wallet*
4. Builds & sends similar transactions from your wallet

---

## 🧰 Structure

```
.
├── bot_copy_trade.py      # Main bot logic
├── Pipfile                # Python dependency manifest
├── Pipfile.lock           # Python dependency manifest locked
├── README.md              # This file
└── .env.example           # Example configuration
```

---

## 🛡️ Security & Disclaimer

Running trading automation tools involves risks:

* Crypto markets are volatile — you may lose funds.
* Exposing private keys to any script can be dangerous.
* Always audit and test in a *safe* environment before use.

By using this software, you agree that you are responsible for any losses or damages.
