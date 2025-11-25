try:
    import pydantic
    print(f"Pydantic version: {pydantic.VERSION}")
except ImportError:
    print("Pydantic not found")
except AttributeError:
    print(f"Pydantic version: {pydantic.__version__}")

try:
    import pydantic_settings
    print(f"Pydantic Settings version: {pydantic_settings.__version__}")
    from pydantic_settings import BaseSettings
    print("BaseSettings imported from pydantic_settings")
except ImportError as e:
    print(f"Pydantic Settings error: {e}")
except Exception as e:
    print(f"Pydantic Settings other error: {e}")

try:
    from pydantic import BaseSettings
    print("BaseSettings imported from pydantic")
except ImportError as e:
    print(f"Pydantic BaseSettings error: {e}")
