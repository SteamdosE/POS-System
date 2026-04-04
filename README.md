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
5. Start the backend server: `python -m src.app`

The app uses **SQLite** for storage (`pos_system.db` is created automatically on first run).

## Usage

### Backend
After installation, the API server runs at `http://localhost:5000`.

### Desktop GUI (Tkinter)
The desktop GUI must be run **after** the backend server is started (it connects to `http://localhost:5000/api`).

Install GUI dependencies first (if not already done):
```bash
pip install -r requirements_gui.txt
```

Then launch the GUI from the repo root with the venv active:
```bash
python -m src.gui.main
```

Alternatively, use the provided entry-point script:
```bash
python run.py
```

## Contributing
Contributions are welcome! Please open an issue or pull request for new features or improvements.

## License
This project is licensed under the MIT License.