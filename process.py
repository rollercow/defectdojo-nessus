import json
import os
import requests
import time
from datetime import datetime, timezone
from dateutil import parser as date_parser

# Nessus config
NESSUS_URL = "https://nessus:8834"
NESSUS_ACCESS_KEY = "36d5db9b04476976608bb1e4601247ff0ed9c27fedc91938283b976f237262e1"
NESSUS_SECRET_KEY = "671646bc6fc3ea3cbbe206ae73e0b3bbb05cf658b14e3a48773ad984c9449df2"
EXPORT_FORMAT = "nessus"

# DefectDojo config
DEFECTDOJO_URL = "http://defectdojo.chi.swan.ac.uk:8080/api/v2"
DEFECTDOJO_API_KEY = "4577632d2b41cece7c0eee3664d5532f093c9894"
SCAN_TYPE = "Tenable Scan"

# Load scan ID to engagement ID mapping
with open("mapping.json", "r") as f:
    scan_engagement_mapping = json.load(f)

# === Nessus session setup ===
session = requests.Session()
session.headers.update(
    {
        "X-ApiKeys": f"accessKey={NESSUS_ACCESS_KEY}; secretKey={NESSUS_SECRET_KEY}",
        "Content-Type": "application/json",
    }
)
session.verify = False

# === DefectDojo auth header ===
defectdojo_headers = {"Authorization": f"Token {DEFECTDOJO_API_KEY}"}

# === Iterate all scans ===
for scan_id, engagement_id in scan_engagement_mapping.items():
    print(f"Processing scan ID {scan_id}...")
    # Fetch scan details to get timestamp
    scan_details = session.get(f"{NESSUS_URL}/scans/{scan_id}")
    scan_details.raise_for_status()
    scan_info = scan_details.json().get("info", {})
    timestamp = scan_info.get("timestamp")
    scan_date = None
    if timestamp:
        scan_date = datetime.utcfromtimestamp(timestamp).replace(tzinfo=timezone.utc)
    else:
        print(f"No timestamp found for scan {scan_id}. Skipping...")
        continue

    # Get most recent test for this engagement and scan type
    resp = requests.get(
        f"{DEFECTDOJO_URL}/tests/?engagement={engagement_id}&scan_type={SCAN_TYPE}",
        headers=defectdojo_headers,
    )
    resp.raise_for_status()
    tests = resp.json().get("results", [])
    test_id = None
    last_scan_date = None

    if tests:
        tests.sort(key=lambda x: x.get("target_end") or "", reverse=True)
        most_recent_test = tests[0]
        test_id = most_recent_test.get("id")
        if most_recent_test.get("target_end"):
            last_scan_date = date_parser.parse(most_recent_test["target_end"])

    # Check if scan_date is newer than the most recently uploaded scan
    if scan_date <= last_scan_date:
        print(
            f"Scan {scan_id} ({scan_date}) is not newer than last uploaded scan ({last_scan_date}). Skipping..."
        )
        continue

    # Request scan export
    export_request = session.post(
        f"{NESSUS_URL}/scans/{scan_id}/export", json={"format": EXPORT_FORMAT}
    )
    export_request.raise_for_status()
    file_id = export_request.json()["file"]

    # Wait until file is ready
    status = ""
    while status != "ready":
        time.sleep(5)
        resp = session.get(f"{NESSUS_URL}/scans/{scan_id}/export/{file_id}/status")
        resp.raise_for_status()
        status = resp.json()["status"]

    # Download file
    filename = f"scan_{scan_id}.{EXPORT_FORMAT}"
    with session.get(
        f"{NESSUS_URL}/scans/{scan_id}/export/{file_id}/download", stream=True
    ) as r:
        r.raise_for_status()
        with open(filename, "wb") as f:
            for chunk in r.iter_content(chunk_size=8192):
                f.write(chunk)
    print(f"Exported scan {scan_id} as {filename}")

    # Prepare request for DefectDojo
    files = {"file": (filename, open(filename, "rb"))}
    data = {"scan_type": SCAN_TYPE}
    if scan_date:
        data["scan_date"] = str(scan_date.date())

    if test_id:
        data["test"] = test_id
        url = f"{DEFECTDOJO_URL}/reimport-scan/"
    else:
        data["engagement"] = engagement_id
        url = f"{DEFECTDOJO_URL}/import-scan/"

    resp = requests.post(url, headers=defectdojo_headers, files=files, data=data)
    resp.raise_for_status()
    action = "reimported into existing test" if test_id else "imported as new test"
    print(f"Successfully {action} for scan {scan_id}.")

    # Clean up
    os.remove(filename)

print("All scans processed successfully!")
