import os

# Your folder path
folder_path = r"C:\Users\mhana\Desktop\aaa analysis\Astra files (2019-2025)"

print("=" * 60)
print("FOLDER DIAGNOSTIC TOOL")
print("=" * 60)
print(f"\nChecking folder: {folder_path}")
print("-" * 60)

# Check if folder exists
if not os.path.exists(folder_path):
    print("❌ ERROR: This folder does NOT exist!")
    print("\nPlease check:")
    print("1. The folder name is spelled correctly")
    print("2. The folder hasn't been moved or deleted")
    exit()

if not os.path.isdir(folder_path):
    print("❌ ERROR: This path exists but is NOT a folder!")
    exit()

print("✅ Folder exists!\n")

# List all files
try:
    all_files = os.listdir(folder_path)
    print(f"Total items in folder: {len(all_files)}\n")
    
    if len(all_files) == 0:
        print("⚠️  The folder is EMPTY!")
        exit()
    
    # Categorize by extension
    file_types = {}
    for item in all_files:
        full_path = os.path.join(folder_path, item)
        if os.path.isfile(full_path):
            ext = os.path.splitext(item)[1].lower()
            if ext == '':
                ext = '(no extension)'
            if ext not in file_types:
                file_types[ext] = []
            file_types[ext].append(item)
    
    # Print results
    print("📁 FILES FOUND:")
    print("-" * 60)
    
    for ext, files in sorted(file_types.items()):
        print(f"\n{ext} files: {len(files)}")
        for f in files[:5]:  # Show first 5 of each type
            print(f"  • {f}")
        if len(files) > 5:
            print(f"  ... and {len(files) - 5} more")
    
    # Check specifically for CSV
    csv_files = [f for f in all_files if f.lower().endswith('.csv')]
    print("\n" + "=" * 60)
    if csv_files:
        print(f"✅ FOUND {len(csv_files)} CSV FILE(S):")
        for csv in csv_files:
            print(f"  • {csv}")
    else:
        print("❌ NO CSV FILES FOUND!")
        print("\nYour files might be:")
        print("  • Excel files (.xlsx or .xls)")
        print("  • Text files (.txt)")
        print("  • In a subfolder")
        print("  • Have a different extension")
    
    print("=" * 60)
    
except Exception as e:
    print(f"❌ ERROR: {str(e)}")
