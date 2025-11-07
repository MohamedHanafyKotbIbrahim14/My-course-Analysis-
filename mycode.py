import os

# PASTE YOUR FOLDER PATH HERE between the quotes:
# Right-click the folder -> "Copy as path" -> Paste below
folder_path = r"C:\Users\mhana\Desktop\aaa analysis\Astra files (2019-2025)"

print("\n" + "="*70)
print("TESTING YOUR FOLDER PATH")
print("="*70)
print(f"\nTrying to access: {folder_path}")
print("-"*70)

# Test 1: Does it exist?
if os.path.exists(folder_path):
    print("✅ SUCCESS! Folder exists!")
else:
    print("❌ FAILED! Folder does NOT exist!")
    print("\nTroubleshooting:")
    print("1. Copy the folder path from Windows Explorer address bar")
    print("2. Right-click folder -> Properties -> Location")
    print("3. Make sure spelling is EXACTLY correct")
    print("\nTry these variations:")
    
    # Try without spaces
    alt1 = folder_path.replace(" ", "")
    if os.path.exists(alt1):
        print(f"✅ Found it without spaces: {alt1}")
    
    input("\nPress Enter to exit...")
    exit()

# Test 2: Is it a folder?
if os.path.isdir(folder_path):
    print("✅ It's a valid folder!")
else:
    print("❌ It exists but it's not a folder!")
    exit()

# Test 3: Can we read it?
try:
    files = os.listdir(folder_path)
    print(f"✅ Can read folder! Found {len(files)} items inside")
    
    # Show first 10 items
    print("\nFirst 10 items:")
    for i, item in enumerate(files[:10], 1):
        item_path = os.path.join(folder_path, item)
        if os.path.isdir(item_path):
            print(f"  {i}. 📁 {item}")
        else:
            ext = os.path.splitext(item)[1]
            print(f"  {i}. 📄 {item} ({ext})")
    
    if len(files) > 10:
        print(f"  ... and {len(files) - 10} more items")
    
    # Count CSV files
    csv_files = [f for f in files if f.lower().endswith('.csv')]
    print(f"\n📊 CSV files found: {len(csv_files)}")
    if csv_files:
        print("CSV files:")
        for csv in csv_files[:5]:
            print(f"  • {csv}")
    
    # Count other common types
    xlsx_files = [f for f in files if f.lower().endswith(('.xlsx', '.xls'))]
    if xlsx_files:
        print(f"\n📗 Excel files found: {len(xlsx_files)}")
    
    print("\n" + "="*70)
    print("✅ YOUR PATH WORKS! Use this in the Streamlit app:")
    print(folder_path)
    print("="*70)
    
except Exception as e:
    print(f"❌ Error reading folder: {e}")

input("\nPress Enter to exit...")
