# POS System Documentation

## Overview
The POS system is designed to streamline retail transactions with a user-friendly interface and robust backend support.

## Features
- **User Management**: Create, manage, and delete users.
- **Inventory Management**: Keep track of stock levels and product details.
- **Sales Processing**: Efficiently process sales transactions with an easy-to-use checkout system.
- **Reporting**: Generate detailed sales reports and analyses.

## Installation
### Requirements
- Python 3.9+
- pip

### Steps
1. Clone the repository: `git clone https://github.com/SteamdosE/POS-System.git`
2. Navigate to the project directory: `cd POS-System`
3. Create and activate a virtual environment:
   - Windows: `python -m venv venv` then `venv\Scripts\activate`
   - macOS/Linux: `python -m venv venv` then `source venv/bin/activate`
4. Install dependencies: `pip install -r requirements.txt`
5. Start the backend server: `python start_backend.py`

The app uses **SQLite** for storage (`pos_system.db` is created automatically on first run).

## Usage
After installation, the API server runs at `http://localhost:5000`.

## Contributing
Contributions are welcome! Please open an issue or pull request for new features or improvements.

## License
This project is licensed under the MIT License.