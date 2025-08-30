## Backtest Backend - Quick Start

### Prerequisites

- Python 3.12 (recommended)
- (Optional) Create and activate a virtual environment:

```
python -m venv env
env\Scripts\activate  # Windows
```

### Install dependencies

```
pip install -r requirements.txt
```

### Run the backend server

```
start_server.bat
```

or

```
python main.py
```

### Notes

- The backend uses FastAPI (see `main.py`).
- The database file is `backtest.db`.
