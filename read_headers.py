import openpyxl

file_path = "dataset/Tasks.xlsx"

try:
    wb = openpyxl.load_workbook(file_path)
    sheet = wb.active
    
    # Read headers (first row)
    headers = []
    for cell in sheet[1]:
        if cell.value:
            headers.append(cell.value)
            
    print("HEADERS_DETECTED:", headers)
    
except Exception as e:
    print(f"Error reading excel: {e}")
