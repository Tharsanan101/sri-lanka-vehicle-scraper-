#!/usr/bin/env python3
"""
Sri Lanka Vehicle Information Scraper - Web Application
Flask web interface for the vehicle information scraper
"""

from flask import Flask, render_template, request, jsonify, send_file, flash, redirect, url_for, session
import os
import json
import csv
import time
from datetime import datetime
import threading
from werkzeug.utils import secure_filename
import zipfile
import io
from vehicle_scraper import VehicleInfoScraper, load_vehicle_numbers_from_csv, load_vehicle_numbers_from_txt

app = Flask(__name__)
app.secret_key = 'your-secret-key-change-this-in-production'
app.config['UPLOAD_FOLDER'] = 'uploads'
app.config['RESULTS_FOLDER'] = 'results'
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024  # 16MB max file size

# Template filters
@app.template_filter('timestamp_to_datetime')
def timestamp_to_datetime(timestamp):
    """Convert timestamp to datetime"""
    try:
        return datetime.fromtimestamp(timestamp)
    except:
        return datetime.now()

@app.template_filter('parse_datetime')
def parse_datetime(datetime_str):
    """Parse ISO datetime string"""
    try:
        return datetime.fromisoformat(datetime_str.replace('Z', '+00:00'))
    except:
        return datetime.now()

@app.template_filter('duration_format')
def duration_format(seconds):
    """Format duration in seconds to human readable format"""
    try:
        hours = int(seconds // 3600)
        minutes = int((seconds % 3600) // 60)
        seconds = int(seconds % 60)
        
        if hours > 0:
            return f"{hours}h {minutes}m {seconds}s"
        elif minutes > 0:
            return f"{minutes}m {seconds}s"
        else:
            return f"{seconds}s"
    except:
        return "Unknown"

@app.context_processor
def inject_current_year():
    """Inject current year into templates"""
    return {'current_year': datetime.now().year}

# Create directories if they don't exist
os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)
os.makedirs(app.config['RESULTS_FOLDER'], exist_ok=True)

# Global variables to track scraping progress
scraping_status = {
    'is_running': False,
    'progress': 0,
    'total': 0,
    'current_vehicle': '',
    'results': [],
    'start_time': None,
    'estimated_time_remaining': None
}

scraping_lock = threading.Lock()


@app.route('/favicon.ico')
def favicon():
    """Serve favicon"""
    return send_file('static/favicon.ico', mimetype='image/vnd.microsoft.icon')


@app.route('/')
def home():
    """Home page with input form"""
    return render_template('index.html')


@app.route('/start_scraping', methods=['POST'])
def start_scraping():
    """Start the scraping process"""
    global scraping_status
    
    with scraping_lock:
        if scraping_status['is_running']:
            return jsonify({'error': 'Scraping is already in progress'}), 400
    
    try:
        # Get form data
        vehicle_input_method = request.form.get('vehicle_input_method')
        session_id = request.form.get('session_id', '').strip()
        max_workers = int(request.form.get('max_workers', 3))
        delay = float(request.form.get('delay', 2.0))
        nic = request.form.get('nic', '2200000000').strip()
        contact = request.form.get('contact', '0777777777').strip()
        
        if not session_id:
            return jsonify({'error': 'Session ID is required'}), 400
        
        # Get vehicle numbers based on input method
        vehicle_numbers = []
        
        if vehicle_input_method == 'manual':
            manual_input = request.form.get('manual_vehicles', '').strip()
            if manual_input:
                vehicle_numbers = [num.strip().upper() for num in manual_input.replace(',', '\n').split('\n') if num.strip()]
        
        elif vehicle_input_method == 'file':
            if 'vehicle_file' not in request.files:
                return jsonify({'error': 'No file uploaded'}), 400
            
            file = request.files['vehicle_file']
            if file.filename == '':
                return jsonify({'error': 'No file selected'}), 400
            
            if file:
                filename = secure_filename(file.filename)
                filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
                file.save(filepath)
                
                # Load vehicle numbers from file
                if filename.lower().endswith('.csv'):
                    vehicle_numbers = load_vehicle_numbers_from_csv(filepath)
                elif filename.lower().endswith('.txt'):
                    vehicle_numbers = load_vehicle_numbers_from_txt(filepath)
                else:
                    return jsonify({'error': 'Unsupported file format. Use CSV or TXT files.'}), 400
                
                # Clean up uploaded file
                os.remove(filepath)
        
        if not vehicle_numbers:
            return jsonify({'error': 'No vehicle numbers provided'}), 400
        
        # Remove duplicates while preserving order
        vehicle_numbers = list(dict.fromkeys(vehicle_numbers))
        
        # Initialize scraping status
        with scraping_lock:
            scraping_status = {
                'is_running': True,
                'progress': 0,
                'total': len(vehicle_numbers),
                'current_vehicle': '',
                'results': [],
                'start_time': time.time(),
                'estimated_time_remaining': None,
                'session_id': session_id
            }
        
        # Start scraping in a separate thread
        scraping_thread = threading.Thread(
            target=run_scraping_task,
            args=(vehicle_numbers, session_id, max_workers, delay, nic, contact)
        )
        scraping_thread.daemon = True
        scraping_thread.start()
        
        return jsonify({
            'message': 'Scraping started successfully',
            'total_vehicles': len(vehicle_numbers)
        })
    
    except Exception as e:
        return jsonify({'error': f'Failed to start scraping: {str(e)}'}), 500


def run_scraping_task(vehicle_numbers, session_id, max_workers, delay, nic, contact):
    """Run the scraping task in a separate thread"""
    global scraping_status
    
    try:
        # Initialize scraper
        scraper = VehicleInfoScraper(
            max_workers=max_workers,
            delay_between_requests=delay,
            fixed_nic=nic,
            fixed_contact=contact,
            jsessionid=session_id
        )
        
        # Process vehicles with progress tracking
        results = []
        
        for i, vehicle_number in enumerate(vehicle_numbers):
            with scraping_lock:
                if not scraping_status['is_running']:  # Check if cancelled
                    break
                
                scraping_status['current_vehicle'] = vehicle_number
                scraping_status['progress'] = i
                
                # Calculate estimated time remaining
                elapsed_time = time.time() - scraping_status['start_time']
                if i > 0:
                    avg_time_per_vehicle = elapsed_time / i
                    remaining_vehicles = len(vehicle_numbers) - i
                    scraping_status['estimated_time_remaining'] = avg_time_per_vehicle * remaining_vehicles
            
            # Get vehicle info
            result = scraper.get_vehicle_info(vehicle_number)
            if result:
                results.append(result)
                
                with scraping_lock:
                    scraping_status['results'] = results.copy()
        
        # Save results
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        csv_filename = f"vehicle_results_{timestamp}.csv"
        json_filename = f"vehicle_results_{timestamp}.json"
        
        csv_path = os.path.join(app.config['RESULTS_FOLDER'], csv_filename)
        json_path = os.path.join(app.config['RESULTS_FOLDER'], json_filename)
        
        scraper.save_results_to_csv(results, csv_path)
        scraper.save_results_to_json(results, json_path)
        
        # Update final status
        with scraping_lock:
            scraping_status.update({
                'is_running': False,
                'progress': len(vehicle_numbers),
                'results': results,
                'csv_file': csv_filename,
                'json_file': json_filename,
                'completed': True
            })
    
    except Exception as e:
        with scraping_lock:
            scraping_status.update({
                'is_running': False,
                'error': str(e),
                'completed': False
            })


@app.route('/progress')
def get_progress():
    """Get current scraping progress"""
    global scraping_status
    
    with scraping_lock:
        status = scraping_status.copy()
    
    # If no scraping has been started, return a default status
    if not status.get('is_running') and not status.get('completed'):
        return jsonify({
            'is_running': False,
            'progress': 0,
            'total': 0,
            'current_vehicle': '',
            'results': [],
            'completed': False
        })
    
    return jsonify(status)


@app.route('/cancel_scraping', methods=['POST'])
def cancel_scraping():
    """Cancel the current scraping process"""
    global scraping_status
    
    with scraping_lock:
        if scraping_status['is_running']:
            scraping_status['is_running'] = False
            return jsonify({'message': 'Scraping cancelled'})
        else:
            return jsonify({'message': 'No scraping process is running'})


@app.route('/results')
def view_results():
    """View scraping results"""
    global scraping_status
    
    with scraping_lock:
        status = scraping_status.copy()
    
    return render_template('results.html', status=status)


@app.route('/download/<filename>')
def download_file(filename):
    """Download result files"""
    try:
        file_path = os.path.join(app.config['RESULTS_FOLDER'], filename)
        if os.path.exists(file_path):
            return send_file(file_path, as_attachment=True)
        else:
            return "File not found", 404
    except Exception as e:
        return f"Error downloading file: {str(e)}", 500


@app.route('/download_all')
def download_all_results():
    """Download all result files as a ZIP"""
    global scraping_status
    
    try:
        with scraping_lock:
            status = scraping_status.copy()
        
        if not status.get('completed'):
            return "No completed results to download", 400
        
        # Create a ZIP file in memory
        memory_file = io.BytesIO()
        
        with zipfile.ZipFile(memory_file, 'w', zipfile.ZIP_DEFLATED) as zf:
            # Add CSV file
            if 'csv_file' in status:
                csv_path = os.path.join(app.config['RESULTS_FOLDER'], status['csv_file'])
                if os.path.exists(csv_path):
                    zf.write(csv_path, status['csv_file'])
            
            # Add JSON file
            if 'json_file' in status:
                json_path = os.path.join(app.config['RESULTS_FOLDER'], status['json_file'])
                if os.path.exists(json_path):
                    zf.write(json_path, status['json_file'])
        
        memory_file.seek(0)
        
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        return send_file(
            memory_file,
            as_attachment=True,
            download_name=f'vehicle_scraper_results_{timestamp}.zip',
            mimetype='application/zip'
        )
    
    except Exception as e:
        return f"Error creating download: {str(e)}", 500


@app.route('/api/validate_session', methods=['POST'])
def validate_session():
    """Validate session ID by making a test request"""
    try:
        session_id = request.json.get('session_id', '').strip()
        if not session_id:
            return jsonify({'valid': False, 'message': 'Session ID is required'})
        
        # Create a test scraper
        test_scraper = VehicleInfoScraper(jsessionid=session_id)
        
        # Make a test request with a dummy vehicle number
        test_result = test_scraper.get_vehicle_info('TEST123')
        
        # Check if the request was successful (even if vehicle doesn't exist)
        if test_result and 'error' not in test_result:
            return jsonify({'valid': True, 'message': 'Session ID appears valid'})
        else:
            return jsonify({'valid': False, 'message': 'Session ID may be invalid or expired'})
    
    except Exception as e:
        return jsonify({'valid': False, 'message': f'Validation error: {str(e)}'})


if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5000)
