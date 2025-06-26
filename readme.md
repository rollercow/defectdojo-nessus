# A mostly 'Vibe' coded script to automate feeding [Nessus](https://www.tenable.com/products/nessus) scans into [DefectDojo](https://defectdojo.com/)

ChatGPT wrote most of this, including this Readme, but stuggled with getting API details correct - (https://chatgpt.com/share/685c606a-981c-8002-bdaf-f6f71423b032)

## Overview

This script automates the process of exporting Nessus scan results and importing them into DefectDojo. The workflow includes:

- Exporting scan results from Nessus.
- Checking if the scan is newer than the last uploaded scan in DefectDojo.
- Importing or reimporting the scan into DefectDojo with the correct scan date.

## Requirements

- **Python 3.6+**
- **`requests` library** for interacting with both the Nessus and DefectDojo APIs.  
  Install it using:  

```bash
 pip install requests
```
- **Nessus API Access**  
You’ll need a Nessus instance with valid **access** and **secret** keys.

- **DefectDojo API Access**  
You’ll need a valid **DefectDojo API key** to authenticate and upload the scans.

## Configuration

### 1. Nessus & DefectDojo

The script assumes you already have a DefectDojo 'engagement' for each nessus scan you wish to load.


### 2. Nessus API Credentials

You will need to set the following Nessus API credentials in the script:

- **NESSUS_URL**: The URL of your Nessus instance (e.g., `https://your-nessus-host:8834`).
- **NESSUS_ACCESS_KEY**: Your Nessus API access key.
- **NESSUS_SECRET_KEY**: Your Nessus API secret key.

### 3. DefectDojo API Credentials

Similarly, configure the following for DefectDojo:

- **DEFECTDOJO_URL**: The URL of your DefectDojo instance (e.g., `https://your-defectdojo-host/api/v2`).
- **DEFECTDOJO_API_KEY**: Your DefectDojo API key to authenticate the uploads.

### 4. Create your Scan to Engagement Mapping File

The script requires a JSON file (`mapping.json`) that maps **scan IDs** from Nessus to the **engagement IDs** in DefectDojo. Here’s an example:

```json
{
"scan_id_1": "engagement_id_1",
"scan_id_2": "engagement_id_2",
"scan_id_3": "engagement_id_3"
}
```

## How It Works
 1.  Fetch Scan Details: The script first fetches the scan details from Nessus using the provided scan ID.

 2. Check Existing Test in DefectDojo: It checks if the scan has been previously uploaded to DefectDojo and compares the scan_date (timestamp of the scan) to determine if the new scan is newer than the existing one.

 3. Export Scan from Nessus: If the scan is newer or hasn't been uploaded yet, the script exports the scan from Nessus.

 4. Reimport or Import Scan into DefectDojo: The script either imports a new scan into DefectDojo or reimports it if it already exists (but the scan is newer).

 5. Cleanup: Temporary files are cleaned up after upload to DefectDojo.

## Usage
### 1. Configure the Script
Ensure you’ve updated the NESSUS_URL, NESSUS_ACCESS_KEY, NESSUS_SECRET_KEY, DEFECTDOJO_URL, and DEFECTDOJO_API_KEY with the appropriate values.

### 2. Prepare the Scan to Engagement Mapping
Make sure you have the mapping.json file with the correct mappings from your Nessus scan IDs to DefectDojo engagement IDs.

### 3. Run the Script
Once everything is set up, run the script in your terminal:

```bash
python nessus_to_defectdojo.py
```

### 4. Check the Results
The script will output information about which scans were processed, skipped, or successfully imported/reimported. You can monitor DefectDojo’s Tests page to see the scans appear in the correct engagement.

