import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), '../backend'))
try:
    from app.config import settings
    print("Config imported successfully")
    print(f"URI: {settings.NEO4J_URI}")
except Exception as e:
    import traceback
    traceback.print_exc()
    print(f"Error: {e}")
