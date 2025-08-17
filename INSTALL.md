# Quick Installation Guide

## Prerequisites
- Python 3.7 or higher
- pip (Python package installer)
- Internet connection

## Installation Steps

### 1. Install Dependencies
```bash
pip install -r requirements.txt
```

### 2. Start the Application

**Option A: Using the start script (Windows)**
```bash
start.bat
```

**Option B: Using Python directly**
```bash
python app.py
```

**Option C: Command Line Interface (Original Script)**
```bash
python vehicle_scraper.py
```

### 3. Access the Web Interface
Open your browser and go to: `http://localhost:5000`

## Quick Start

1. **Get Session ID**: 
   - Open the Sri Lanka Motor Traffic website in your browser
   - Login if required
   - Press F12 → Application → Cookies → Copy JSESSIONID value

2. **Input Vehicle Numbers**:
   - Enter manually: `ABC-1234, DEF-5678`
   - Or upload a CSV/TXT file

3. **Configure Settings**:
   - Max workers: 3 (recommended)
   - Delay: 2.0 seconds (recommended)

4. **Start Scraping** and monitor progress

5. **Download Results** as CSV, JSON, or ZIP

## Troubleshooting

- **Import errors**: Run `pip install -r requirements.txt`
- **Port in use**: Change port in `app.py` (line: `app.run(port=5001)`)
- **Session invalid**: Get a fresh JSESSIONID from your browser

## Need Help?
Check the main README.md file for detailed instructions.
