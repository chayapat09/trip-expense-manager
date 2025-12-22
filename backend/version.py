import hashlib
import os

def get_db_version() -> str:
    """
    Get the database version based on the SHA256 hash of the database.py file.
    This ensures that any change to the schema code results in a new version.
    Returns the first 8 characters of the hash.
    """
    try:
        # Assuming database.py is in the same directory as this file
        db_file_path = os.path.join(os.path.dirname(__file__), "database.py")
        
        if not os.path.exists(db_file_path):
            return "unknown-missing-file"
            
        with open(db_file_path, "rb") as f:
            file_content = f.read()
            
        sha256_hash = hashlib.sha256(file_content).hexdigest()
        return sha256_hash[:8]
        
    except Exception as e:
        print(f"Error calculating DB version: {e}")
        return "unknown-error"

APP_VERSION = get_db_version()
