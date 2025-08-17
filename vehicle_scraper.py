#!/usr/bin/env python3
"""
Sri Lanka Vehicle Information Scraper - Core Module
Multithreaded script to retrieve vehicle information from eservices.motortraffic.gov.lk
"""

import requests
import threading
import time
import json
import csv
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import datetime
import logging
from typing import List, Dict, Optional
import urllib3
from bs4 import BeautifulSoup
import re
import os

# Disable SSL warnings since the original curl uses --insecure
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

# Configure logging
logger = logging.getLogger(__name__)


class VehicleInfoScraper:
    def __init__(self, max_workers: int = 5, delay_between_requests: float = 1.0,
                 fixed_nic: str = "2200000000", fixed_contact: str = "0777777777",
                 jsessionid: str = None):
        """
        Initialize the scraper

        Args:
            max_workers: Maximum number of concurrent threads
            delay_between_requests: Delay between requests in seconds
            fixed_nic: Fixed NIC number to use for all requests
            fixed_contact: Fixed contact number to use for all requests
            jsessionid: Session ID cookie for authentication
        """
        self.max_workers = max_workers
        self.delay_between_requests = delay_between_requests
        self.fixed_nic = fixed_nic
        self.fixed_contact = fixed_contact
        self.base_url = "https://eservices.motortraffic.gov.lk/VehicleInfo/retrieveLimitedVehicleInformation.action"
        self.results = []
        self.failed_requests = []
        self.lock = threading.Lock()

        # Headers from your curl request
        self.headers = {
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.7',
            'Accept-Language': 'en-US,en;q=0.9',
            'Cache-Control': 'max-age=0',
            'Connection': 'keep-alive',
            'Content-Type': 'application/x-www-form-urlencoded',
            'Origin': 'https://eservices.motortraffic.gov.lk',
            'Referer': 'https://eservices.motortraffic.gov.lk/VehicleInfo/indexOauth.action',
            'Sec-Fetch-Dest': 'document',
            'Sec-Fetch-Mode': 'navigate',
            'Sec-Fetch-Site': 'same-origin',
            'Sec-Fetch-User': '?1',
            'Upgrade-Insecure-Requests': '1',
            'User-Agent': 'Mozilla/5.0 (Linux; Android 6.0; Nexus 5 Build/MRA58N) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/139.0.0.0 Mobile Safari/537.36 Edg/139.0.0.0',
            'sec-ch-ua': '"Not;A=Brand";v="99", "Microsoft Edge";v="139", "Chromium";v="139"',
            'sec-ch-ua-mobile': '?1',
            'sec-ch-ua-platform': '"Android"'
        }

        # Cookies - now using the provided session ID
        self.cookies = {
            'f5_cspm': '1234',
            'JSESSIONID': jsessionid or 'F750F4D0BE39C97D2AB19DF9148798B8',
        }

    def parse_vehicle_info(self, html_content: str, vehicle_number: str) -> Dict:
        """
        Parse vehicle information from HTML response

        Args:
            html_content: HTML response content
            vehicle_number: Vehicle registration number

        Returns:
            Dictionary with parsed vehicle information
        """
        try:
            soup = BeautifulSoup(html_content, 'html.parser')

            # Initialize result dictionary
            result = {
                'vehicle_number': vehicle_number,
                'report_date': '',
                'name_of_ownership': '',
                'engine_number': '',
                'vehicle_class': '',
                'conditions_and_notes': '',
                'make': '',
                'model': '',
                'year_of_manufacture': '',
                'status': 'success',
                'timestamp': datetime.now().isoformat()
            }

            # Extract report date
            report_date_elem = soup.find('label', text=re.compile(r'Report Date\s*:'))
            if report_date_elem:
                parent = report_date_elem.parent
                if parent:
                    date_text = parent.get_text(strip=True)
                    date_match = re.search(r'Report Date\s*:\s*(.+)', date_text)
                    if date_match:
                        result['report_date'] = date_match.group(1).strip()

            # Extract vehicle registration number (for verification)
            vehicle_reg_elem = soup.find('label', text=re.compile(r'Vehicle Registration Number\s*:'))
            if vehicle_reg_elem:
                parent = vehicle_reg_elem.parent
                if parent:
                    reg_text = parent.get_text(strip=True)
                    reg_match = re.search(r'Vehicle Registration Number\s*:\s*(.+)', reg_text)
                    if reg_match:
                        extracted_vehicle_num = reg_match.group(1).strip()
                        if extracted_vehicle_num != vehicle_number:
                            logger.warning(f"Vehicle number mismatch: requested {vehicle_number}, got {extracted_vehicle_num}")

            # Extract information from the details table
            table = soup.find('table', class_='table table-striped table-condensed')
            if table:
                rows = table.find_all('tr')

                for row in rows:
                    cells = row.find_all('td')
                    if len(cells) >= 3:
                        label_cell = cells[0]
                        value_cell = cells[2]

                        label_text = label_cell.get_text(strip=True).lower()
                        value_text = value_cell.get_text(strip=True)

                        # Map labels to result fields
                        if 'name of the absolute ownership' in label_text or 'mortgage if any' in label_text:
                            result['name_of_ownership'] = value_text
                        elif 'engine number' in label_text:
                            result['engine_number'] = value_text
                        elif 'vehicle class' in label_text:
                            result['vehicle_class'] = value_text
                        elif 'conditions and notes' in label_text:
                            result['conditions_and_notes'] = value_text
                        elif 'make' in label_text and 'year' not in label_text:
                            result['make'] = value_text
                        elif 'model' in label_text:
                            result['model'] = value_text
                        elif 'year of manufacture' in label_text:
                            result['year_of_manufacture'] = value_text

            return result

        except Exception as e:
            logger.error(f"Error parsing HTML for {vehicle_number}: {str(e)}")
            return {
                'vehicle_number': vehicle_number,
                'status': 'parse_error',
                'error': f"HTML parsing failed: {str(e)}",
                'timestamp': datetime.now().isoformat()
            }

    def get_vehicle_info(self, vehicle_number: str) -> Optional[Dict]:
        """
        Get vehicle information for a single vehicle

        Args:
            vehicle_number: Vehicle registration number

        Returns:
            Dictionary with vehicle information or None if failed
        """
        try:
            # Add delay between requests
            time.sleep(self.delay_between_requests)

            # Prepare form data with fixed NIC and contact number
            data = {
                'nicNumber': self.fixed_nic,
                'contactNumber': self.fixed_contact,
                'vehicleRegistrationNumber': vehicle_number
            }

            # Make the request
            response = requests.post(
                self.base_url,
                headers=self.headers,
                cookies=self.cookies,
                data=data,
                verify=False,  # Equivalent to --insecure
                timeout=30
            )

            if response.status_code == 200:
                # Parse the HTML response to extract vehicle information
                parsed_info = self.parse_vehicle_info(response.text, vehicle_number)

                logger.info(f"Successfully retrieved info for {vehicle_number}")
                return parsed_info
            else:
                logger.error(f"Failed to retrieve info for {vehicle_number}: HTTP {response.status_code}")
                return {
                    'vehicle_number': vehicle_number,
                    'status': 'failed',
                    'error': f"HTTP {response.status_code}",
                    'timestamp': datetime.now().isoformat()
                }

        except Exception as e:
            logger.error(f"Exception for {vehicle_number}: {str(e)}")
            return {
                'vehicle_number': vehicle_number,
                'status': 'failed',
                'error': str(e),
                'timestamp': datetime.now().isoformat()
            }

    def process_vehicles(self, vehicle_numbers: List[str]) -> List[Dict]:
        """
        Process multiple vehicles using threading

        Args:
            vehicle_numbers: List of vehicle registration numbers

        Returns:
            List of results
        """
        results = []

        with ThreadPoolExecutor(max_workers=self.max_workers) as executor:
            # Submit all tasks
            future_to_vehicle = {
                executor.submit(self.get_vehicle_info, vehicle_number): vehicle_number
                for vehicle_number in vehicle_numbers
            }

            # Process completed tasks
            for future in as_completed(future_to_vehicle):
                vehicle_number = future_to_vehicle[future]
                try:
                    result = future.result()
                    if result:
                        results.append(result)
                except Exception as exc:
                    logger.error(f'Vehicle {vehicle_number} generated an exception: {exc}')
                    results.append({
                        'vehicle_number': vehicle_number,
                        'status': 'failed',
                        'error': str(exc),
                        'timestamp': datetime.now().isoformat()
                    })

        return results

    def save_results_to_csv(self, results: List[Dict], filename: str = None):
        """Save results to CSV file"""
        if not filename:
            filename = f"vehicle_results_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv"

        if not results:
            logger.warning("No results to save")
            return

        with open(filename, 'w', newline='', encoding='utf-8') as csvfile:
            fieldnames = [
                'vehicle_number', 'report_date', 'name_of_ownership', 'engine_number',
                'vehicle_class', 'conditions_and_notes', 'make', 'model',
                'year_of_manufacture', 'status', 'timestamp', 'error'
            ]
            writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
            writer.writeheader()

            for result in results:
                writer.writerow(result)

        logger.info(f"Results saved to {filename}")

    def save_results_to_json(self, results: List[Dict], filename: str = None):
        """Save results to JSON file"""
        if not filename:
            filename = f"vehicle_results_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"

        with open(filename, 'w', encoding='utf-8') as jsonfile:
            json.dump(results, jsonfile, indent=2, ensure_ascii=False)

        logger.info(f"Results saved to {filename}")


def load_vehicle_numbers_from_csv(filename: str) -> List[str]:
    """
    Load vehicle numbers from CSV file
    Expected column: vehicle_number
    """
    vehicle_numbers = []
    try:
        with open(filename, 'r', encoding='utf-8') as csvfile:
            reader = csv.DictReader(csvfile)
            for row in reader:
                if 'vehicle_number' in row:
                    vehicle_numbers.append(row['vehicle_number'])
                else:
                    # If no header, assume first column is vehicle number
                    vehicle_numbers.append(list(row.values())[0])
        logger.info(f"Loaded {len(vehicle_numbers)} vehicle numbers from {filename}")
    except Exception as e:
        logger.error(f"Error loading vehicle numbers from CSV: {e}")

    return vehicle_numbers


def load_vehicle_numbers_from_txt(filename: str) -> List[str]:
    """
    Load vehicle numbers from text file (one per line)
    """
    vehicle_numbers = []
    try:
        with open(filename, 'r', encoding='utf-8') as file:
            for line in file:
                vehicle_number = line.strip()
                if vehicle_number:
                    vehicle_numbers.append(vehicle_number)
        logger.info(f"Loaded {len(vehicle_numbers)} vehicle numbers from {filename}")
    except Exception as e:
        logger.error(f"Error loading vehicle numbers from text file: {e}")

    return vehicle_numbers


# CLI functions for backward compatibility
def get_user_input_for_vehicles() -> List[str]:
    """Get vehicle numbers from user input"""
    print("\n" + "="*60)
    print("VEHICLE NUMBER INPUT")
    print("="*60)
    print("Choose how you want to provide vehicle numbers:")
    print("1. Enter manually (one by one)")
    print("2. Enter multiple at once (comma-separated)")
    print("3. Load from CSV file")
    print("4. Load from text file")
    
    while True:
        choice = input("\nEnter your choice (1-4): ").strip()
        
        if choice == '1':
            return get_manual_vehicle_input()
        elif choice == '2':
            return get_comma_separated_vehicle_input()
        elif choice == '3':
            return get_csv_file_input()
        elif choice == '4':
            return get_txt_file_input()
        else:
            print("Invalid choice. Please enter 1, 2, 3, or 4.")


def get_manual_vehicle_input() -> List[str]:
    """Get vehicle numbers one by one from user"""
    vehicle_numbers = []
    print("\nEnter vehicle numbers one by one (press Enter with empty input to finish):")
    
    while True:
        vehicle_num = input(f"Vehicle #{len(vehicle_numbers) + 1}: ").strip().upper()
        if not vehicle_num:
            break
        vehicle_numbers.append(vehicle_num)
        print(f"Added: {vehicle_num}")
    
    return vehicle_numbers


def get_comma_separated_vehicle_input() -> List[str]:
    """Get comma-separated vehicle numbers from user"""
    while True:
        user_input = input("\nEnter vehicle numbers separated by commas: ").strip()
        if user_input:
            vehicle_numbers = [num.strip().upper() for num in user_input.split(',') if num.strip()]
            print(f"Found {len(vehicle_numbers)} vehicle numbers:")
            for i, num in enumerate(vehicle_numbers, 1):
                print(f"  {i}. {num}")
            
            confirm = input("\nIs this correct? (y/n): ").strip().lower()
            if confirm in ['y', 'yes']:
                return vehicle_numbers
        else:
            print("Please enter at least one vehicle number.")


def get_csv_file_input() -> List[str]:
    """Get vehicle numbers from CSV file"""
    while True:
        filename = input("\nEnter CSV filename (or full path): ").strip()
        if os.path.exists(filename):
            vehicle_numbers = load_vehicle_numbers_from_csv(filename)
            if vehicle_numbers:
                print(f"Successfully loaded {len(vehicle_numbers)} vehicle numbers from {filename}")
                return vehicle_numbers
            else:
                print("No vehicle numbers found in the CSV file.")
        else:
            print(f"File '{filename}' not found.")
            retry = input("Try again? (y/n): ").strip().lower()
            if retry not in ['y', 'yes']:
                return []


def get_txt_file_input() -> List[str]:
    """Get vehicle numbers from text file"""
    while True:
        filename = input("\nEnter text filename (or full path): ").strip()
        if os.path.exists(filename):
            vehicle_numbers = load_vehicle_numbers_from_txt(filename)
            if vehicle_numbers:
                print(f"Successfully loaded {len(vehicle_numbers)} vehicle numbers from {filename}")
                return vehicle_numbers
            else:
                print("No vehicle numbers found in the text file.")
        else:
            print(f"File '{filename}' not found.")
            retry = input("Try again? (y/n): ").strip().lower()
            if retry not in ['y', 'yes']:
                return []


def get_session_cookie() -> str:
    """Get session cookie from user"""
    print("\n" + "="*60)
    print("SESSION COOKIE INPUT")
    print("="*60)
    print("You need to provide a valid JSESSIONID cookie from your browser.")
    print("To get this:")
    print("1. Open your browser and go to the vehicle info website")
    print("2. Login/authenticate if required")
    print("3. Open Developer Tools (F12)")
    print("4. Go to Application/Storage tab > Cookies")
    print("5. Find the JSESSIONID value")
    print("\nExample: F750F4D0BE39C97D2AB19DF9148798B8")
    
    while True:
        session_id = input("\nEnter JSESSIONID: ").strip()
        if session_id:
            print(f"Session ID set: {session_id[:10]}...{session_id[-10:]}")
            return session_id
        else:
            print("Session ID cannot be empty.")


def get_configuration() -> Dict:
    """Get scraper configuration from user"""
    print("\n" + "="*60)
    print("SCRAPER CONFIGURATION")
    print("="*60)
    
    # Get max workers
    while True:
        try:
            max_workers = input("Maximum concurrent threads (default 3): ").strip()
            max_workers = int(max_workers) if max_workers else 3
            if 1 <= max_workers <= 10:
                break
            else:
                print("Please enter a number between 1 and 10.")
        except ValueError:
            print("Please enter a valid number.")
    
    # Get delay
    while True:
        try:
            delay = input("Delay between requests in seconds (default 2.0): ").strip()
            delay = float(delay) if delay else 2.0
            if 0.1 <= delay <= 10.0:
                break
            else:
                print("Please enter a number between 0.1 and 10.0.")
        except ValueError:
            print("Please enter a valid number.")
    
    # Get NIC and contact (optional, with defaults)
    print("\nOptional: Enter custom NIC and contact number")
    print("(Leave empty to use defaults)")
    
    nic = input("NIC number (default: 2200000000): ").strip()
    nic = nic if nic else "2200000000"
    
    contact = input("Contact number (default: 0777777777): ").strip()
    contact = contact if contact else "0777777777"
    
    return {
        'max_workers': max_workers,
        'delay': delay,
        'nic': nic,
        'contact': contact
    }


def main():
    """Main function with user interaction"""
    print("="*60)
    print("SRI LANKA VEHICLE INFORMATION SCRAPER")
    print("="*60)
    print("This tool scrapes vehicle information from the")
    print("Sri Lanka Motor Traffic Department website.")
    print("\nIMPORTANT: Use responsibly and ensure you have")
    print("permission to access this data.")
    print("="*60)

    # Get vehicle numbers from user
    vehicle_numbers = get_user_input_for_vehicles()
    
    if not vehicle_numbers:
        print("No vehicle numbers provided. Exiting.")
        return

    # Get session cookie
    session_cookie = get_session_cookie()
    
    # Get configuration
    config = get_configuration()
    
    # Display summary
    print("\n" + "="*60)
    print("SUMMARY")
    print("="*60)
    print(f"Vehicle numbers to process: {len(vehicle_numbers)}")
    print(f"Max concurrent threads: {config['max_workers']}")
    print(f"Delay between requests: {config['delay']} seconds")
    print(f"NIC: {config['nic']}")
    print(f"Contact: {config['contact']}")
    print(f"Session ID: {session_cookie[:10]}...{session_cookie[-10:]}")
    
    # Confirm before starting
    print("\nVehicle numbers to process:")
    for i, num in enumerate(vehicle_numbers[:10], 1):  # Show first 10
        print(f"  {i}. {num}")
    if len(vehicle_numbers) > 10:
        print(f"  ... and {len(vehicle_numbers) - 10} more")
    
    confirm = input(f"\nProceed with scraping {len(vehicle_numbers)} vehicles? (y/n): ").strip().lower()
    if confirm not in ['y', 'yes']:
        print("Operation cancelled.")
        return

    # Initialize scraper
    scraper = VehicleInfoScraper(
        max_workers=config['max_workers'],
        delay_between_requests=config['delay'],
        fixed_nic=config['nic'],
        fixed_contact=config['contact'],
        jsessionid=session_cookie
    )

    logger.info(f"Starting to process {len(vehicle_numbers)} vehicles")
    start_time = time.time()

    # Process all vehicles
    results = scraper.process_vehicles(vehicle_numbers)

    end_time = time.time()
    logger.info(f"Processing completed in {end_time - start_time:.2f} seconds")

    # Count successful and failed requests
    successful = len([r for r in results if r['status'] == 'success'])
    failed = len(results) - successful

    logger.info(f"Results: {successful} successful, {failed} failed")

    # Save results
    scraper.save_results_to_csv(results)
    scraper.save_results_to_json(results)

    # Display summary of successful results
    print(f"\n" + "="*60)
    print("RESULTS SUMMARY")
    print("="*60)
    print(f"Total vehicles processed: {len(results)}")
    print(f"Successful: {successful}")
    print(f"Failed: {failed}")
    print(f"Success rate: {(successful/len(results)*100):.1f}%")

    if successful > 0:
        print(f"\nSample successful results:")
        print("-" * 60)
        sample_count = min(5, successful)
        shown = 0
        for result in results:
            if result['status'] == 'success' and shown < sample_count:
                print(f"Vehicle: {result['vehicle_number']}")
                print(f"  Make/Model: {result['make']} {result['model']}")
                print(f"  Year: {result['year_of_manufacture']}")
                print(f"  Engine: {result['engine_number']}")
                print(f"  Class: {result['vehicle_class']}")
                if result['name_of_ownership']:
                    print(f"  Owner/Mortgage: {result['name_of_ownership'][:50]}...")
                print("-" * 40)
                shown += 1
        
        if successful > sample_count:
            print(f"... and {successful - sample_count} more successful results")
    
    print(f"\nResults saved to CSV and JSON files.")
    print("Check the log file 'vehicle_scraper.log' for detailed information.")


if __name__ == "__main__":
    # Configure logging for CLI mode
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(levelname)s - %(message)s',
        handlers=[
            logging.FileHandler('vehicle_scraper.log'),
            logging.StreamHandler()
        ]
    )
    
    main()
