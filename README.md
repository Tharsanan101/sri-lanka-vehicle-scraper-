# Sri Lanka Vehicle Information Scraper - Web Application

A modern web interface for scraping vehicle information from the Sri Lanka Motor Traffic Department website. This application provides an easy-to-use web interface for the original command-line scraper script.

## ⚠️ Important Notice

**Use this tool responsibly and ensure you have permission to access the data.** This tool is for educational and legitimate purposes only. Users are responsible for complying with all applicable laws and the website's terms of service.

## 🚀 Features

- **Modern Web Interface**: Clean, responsive design with Bootstrap 5
- **Real-time Progress Tracking**: Live updates during scraping operations
- **Multiple Input Methods**: Manual input, comma-separated, or file upload (CSV/TXT)
- **Session Management**: Easy session cookie validation
- **Export Options**: Download results as CSV, JSON, or ZIP
- **Detailed Results**: Comprehensive vehicle information display
- **Error Handling**: Robust error handling and user feedback
- **Mobile Responsive**: Works on desktop, tablet, and mobile devices

## 📋 Requirements

- Python 3.7 or higher
- Valid JSESSIONID from the vehicle information website
- Internet connection

## 🛠️ Installation

### 1. Clone or Download

```bash
# Clone the repository (if using git)
git clone <repository-url>

# Or download and extract the ZIP file
```

### 2. Install Dependencies

```bash
# Navigate to the project directory
cd RMV

# Install required packages
pip install -r requirements.txt
```

### 3. Run the Application

```bash
# Start the Flask application
python app.py
```

The application will start on `http://localhost:5000`

## 🔧 Configuration

### Environment Variables (Optional)

Create a `.env` file in the project root for custom configuration:

```env
FLASK_SECRET_KEY=your-secret-key-here
FLASK_DEBUG=True
FLASK_HOST=0.0.0.0
FLASK_PORT=5000
MAX_UPLOAD_SIZE=16777216  # 16MB in bytes
```

### Default Settings

- **Max Workers**: 3 concurrent threads
- **Request Delay**: 2.0 seconds between requests
- **Upload Limit**: 16MB
- **Default NIC**: 2200000000
- **Default Contact**: 0777777777

## 📖 How to Use

### Step 1: Get Session Cookie

1. Open your web browser
2. Navigate to the Sri Lanka Motor Traffic Department vehicle information website
3. Login or authenticate if required
4. Open Developer Tools (F12)
5. Go to Application/Storage → Cookies
6. Find and copy the `JSESSIONID` value

### Step 2: Access the Web Application

1. Open your browser and go to `http://localhost:5000`
2. Enter the Session ID (JSESSIONID) in the configuration section
3. Optionally validate the session ID using the "Validate" button

### Step 3: Input Vehicle Numbers

Choose one of the input methods:

**Manual Input:**
- Enter vehicle numbers in the text area
- One per line or comma-separated
- Example: `ABC-1234, DEF-5678`

**File Upload:**
- Upload a CSV or TXT file
- Each line should contain one vehicle number
- CSV files should have a `vehicle_number` column

### Step 4: Configure Scraper

Adjust settings as needed:
- **Max Workers**: Number of concurrent threads (1-5)
- **Delay**: Time between requests (0.5-5.0 seconds)
- **NIC/Contact**: Fixed values for requests

### Step 5: Start Scraping

1. Click "Start Scraping"
2. Monitor real-time progress
3. View results when complete

## 📊 Understanding Results

### Vehicle Information Fields

- **Vehicle Number**: Registration number
- **Make & Model**: Vehicle manufacturer and model
- **Year**: Year of manufacture
- **Engine Number**: Engine identification number
- **Vehicle Class**: Classification (e.g., Motor Car, Motor Cycle)
- **Owner/Mortgage**: Ownership or mortgage information
- **Report Date**: Date of the report
- **Conditions & Notes**: Additional information

### Status Types

- **Success**: Information retrieved successfully
- **Failed**: Request failed (network, authentication, or parsing error)

## 📁 File Structure

```
RMV/
├── app.py                 # Main Flask application
├── vehicle_scraper.py     # Core scraper logic
├── requirements.txt       # Python dependencies
├── README.md             # This file
├── templates/            # HTML templates
│   ├── base.html
│   ├── index.html
│   └── results.html
├── static/               # Static files
│   ├── css/
│   │   └── style.css
│   └── js/
│       └── main.js
├── uploads/              # Temporary file uploads
└── results/              # Generated result files
```

## 🔍 API Endpoints

The application provides several API endpoints:

- `GET /` - Home page
- `POST /start_scraping` - Start scraping process
- `GET /progress` - Get current progress
- `POST /cancel_scraping` - Cancel scraping
- `GET /results` - View results page
- `GET /download/<filename>` - Download specific file
- `GET /download_all` - Download all results as ZIP
- `POST /api/validate_session` - Validate session ID

## 🛡️ Security Considerations

1. **Session Management**: Session IDs are not stored permanently
2. **File Uploads**: Limited to 16MB and specific file types
3. **Input Validation**: Vehicle numbers and session IDs are validated
4. **Rate Limiting**: Built-in delays prevent overwhelming the target server
5. **HTTPS**: Use HTTPS in production environments

## 🔧 Troubleshooting

### Common Issues

1. **"Session ID Invalid"**
   - Ensure you have a fresh, valid JSESSIONID
   - Try logging into the website again and getting a new session ID

2. **"No Results Found"**
   - Check vehicle number format (ABC-1234 or 12-3456)
   - Verify the vehicle exists in the database

3. **"Connection Errors"**
   - Check your internet connection
   - The target website might be temporarily unavailable

4. **"File Upload Issues"**
   - Ensure file is CSV or TXT format
   - Check file size (max 16MB)
   - Verify file contains valid vehicle numbers

### Performance Tips

1. **Optimal Settings**:
   - Use 3-5 max workers for best performance
   - 2-3 second delay between requests to avoid rate limiting

2. **Large Datasets**:
   - For 100+ vehicles, consider running during off-peak hours
   - Monitor progress and be prepared to resume if needed

## 🚀 Production Deployment

### Using Gunicorn (Recommended)

```bash
# Install gunicorn
pip install gunicorn

# Run with gunicorn
gunicorn -w 4 -b 0.0.0.0:5000 app:app
```

### Using Docker

Create a `Dockerfile`:

```dockerfile
FROM python:3.9-slim

WORKDIR /app
COPY requirements.txt .
RUN pip install -r requirements.txt

COPY . .

EXPOSE 5000
CMD ["gunicorn", "-w", "4", "-b", "0.0.0.0:5000", "app:app"]
```

### Environment Variables for Production

```env
FLASK_ENV=production
FLASK_DEBUG=False
FLASK_SECRET_KEY=your-secure-secret-key
```

## 📝 License

This project is for educational purposes. Please ensure compliance with all applicable laws and website terms of service.

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Test thoroughly
5. Submit a pull request

## 📞 Support

For issues or questions:

1. Check the troubleshooting section
2. Review the application logs
3. Ensure you have the latest version

## 🔄 Version History

- **v1.0.0**: Initial web application release
  - Modern Flask web interface
  - Real-time progress tracking
  - Multiple input methods
  - Export functionality

## ⚡ Quick Start

```bash
# 1. Install dependencies
pip install -r requirements.txt

# 2. Start the application
python app.py

# 3. Open browser to http://localhost:5000

# 4. Enter your session ID and vehicle numbers

# 5. Start scraping and download results
```

---

**Remember**: Always use this tool responsibly and in compliance with applicable laws and website terms of service.
