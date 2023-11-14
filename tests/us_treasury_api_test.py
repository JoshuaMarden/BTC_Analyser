from requests.adapters import HTTPAdapter
from requests.packages.urllib3.util.retry import Retry
import requests

retry_strategy = Retry(
    total=3,
    status_forcelist=[429, 500, 502, 503, 504],
    allowed_methods=["HEAD", "GET", "OPTIONS"],
    backoff_factor=1
)

adapter = HTTPAdapter(max_retries=retry_strategy)
http = requests.Session()
http.mount("https://", adapter)

try:
    response = http.get('https://www.transparency.treasury.gov/services/api/fiscal_service/v1/accounting/od/debt_to_penny')
    # Your code to process the response
except requests.exceptions.ConnectionError as e:
    print(f"Connection failed: {e}")
except requests.exceptions.Timeout as e:
    print(f"Request timed out: {e}")
except requests.exceptions.RequestException as e:
    print(f"Request exception: {e}")
