from scan_engine import ScanEngine
from services.target_security import validate_target_url
scan_engine = ScanEngine(validate_target_url)
