
import os

env_path = ".env"

if os.path.exists(env_path):
    with open(env_path, "rb") as f:
        content = f.read()
    
    print(f"Original content length: {len(content)}")
    print(f"Original start: {content[:20]}")

    # Try to decode
    decoded = ""
    try:
        # Check if it has BOM for UTF-16LE
        if content.startswith(b'\xff\xfe'):
            print("Detected UTF-16LE BOM")
            decoded = content.decode('utf-16-le')
        else:
            # Maybe mixed content?
            # If I appended utf-16 to utf-8 file, it's corrupt.
            # But usually >> in PS appends in output encoding.
            # If the file was UTF-8 before?
            
            # Let's try to decode as utf-8 ignoring errors
            try:
                decoded = content.decode('utf-8')
            except UnicodeDecodeError:
                # If it fails, maybe it matches the 'mixed' hypothesis
                print("UTF-8 decode failed. Attempting rescue.")
                
                # If I appended, the new part is likely at end.
                # Let's just try to read line by line or clean null bytes?
                # A simple heuristic: remove null bytes if mostly ascii
                clean_content = content.replace(b'\x00', b'')
                decoded = clean_content.decode('utf-8', errors='ignore')

    except Exception as e:
        print(f"Error decoding: {e}")
        decoded = content.decode('utf-8', errors='ignore')

    print("Decoded contentPreview:")
    print(decoded[:500])

    # Write back as UTF-8
    with open(env_path, "w", encoding="utf-8") as f:
        f.write(decoded.strip() + "\n")
    
    print("Fixed .env encoding to UTF-8")

else:
    print(".env not found")
