#!/usr/bin/env python
"""Test CSV export functionality with headers and title"""

import re
from datetime import datetime

# Test data similar to SO2F2 Analyzer format
test_data = """Sr.No   Date     Time   Conc  Temp  Flow 
------- ---------- ------ ----- ----- ----- 
1       29/04/26   12:14  85.2  28.5  15.3
2       29/04/26   12:15  86.1  28.6  15.2
3       29/04/26   12:16  84.9  28.4  15.1"""

# Parse the data
lines = test_data.split('\n')
lines = [line for line in lines if line.strip()]

print("All lines:")
for i, line in enumerate(lines):
    print(f"  {i}: {repr(line)}")

# Find and extract header line
header_row = None
data_start_idx = 0
for idx, line in enumerate(lines):
    if line.strip().startswith('Sr.No'):
        # This is the header line
        header_line = line
        print(f"\nFound header at index {idx}: {repr(header_line)}")
        
        # Parse headers from this line
        delimiter = None
        if '\t' in header_line:
            delimiter = '\t'
        elif ',' in header_line:
            delimiter = ','
        
        if delimiter:
            header_row = [col.strip() for col in header_line.split(delimiter) if col.strip()]
        else:
            header_row = [col for col in re.split(r'\s{2,}|\s*\t\s*', header_line.strip()) if col.strip()]
        
        print(f"Parsed headers: {header_row}")
        
        # Data starts after the separator line
        if idx + 1 < len(lines) and '---' in lines[idx + 1]:
            data_start_idx = idx + 2
        else:
            data_start_idx = idx + 1
        break

print(f"\nData starts at index: {data_start_idx}")

# Detect delimiter from data
delimiter = None
for line in lines[data_start_idx:]:
    if '\t' in line:
        delimiter = '\t'
        break
    elif ',' in line:
        delimiter = ','
        break

print(f"Delimiter detected: {repr(delimiter)}")

# Parse data
parsed_data = []

for line in lines[data_start_idx:]:
    # Skip separator lines
    if re.match(r'^\s*-+\s*(-\s*)*$', line.strip()):
        print(f"Skipping separator: {line.strip()}")
        continue
    
    if delimiter:
        cols = [col.strip() for col in line.split(delimiter) if col.strip()]
    else:
        # Split on multiple spaces
        cols = [col for col in re.split(r'\s{2,}|\s*\t\s*', line.strip()) if col.strip()]
    
    if cols:
        parsed_data.append(cols)
        print(f"Parsed row: {cols}")

print(f"\nTotal data rows: {len(parsed_data)}")

# Write CSV with headers and title
try:
    output_file = "d:\\spyder_pro\\p1\\test_export_with_headers.csv"
    with open(output_file, 'w', newline='', encoding='utf-8') as csvfile:
        # Write title
        csvfile.write("Serial Port Data Export\n")
        csvfile.write(f"Exported,{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
        csvfile.write(f"Port,COM3 @ 9600 bps\n")
        csvfile.write("\n")
        
        # Write header row if found
        if header_row:
            csvfile.write(','.join(header_row) + '\n')
        
        # Write data rows
        for row in parsed_data:
            csvfile.write(','.join(row) + '\n')
    
    print(f"\nSuccessfully created CSV file: {output_file}")
    
    # Read and display
    print("\nCSV Content:")
    with open(output_file, 'r', encoding='utf-8') as f:
        print(f.read())
        
except Exception as e:
    print(f"\nError creating CSV file: {str(e)}")
    import traceback
    traceback.print_exc()


