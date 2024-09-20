# data_cache.py
import time
from threading import Lock
from your_plot_module import fetch_option_data

# Global cache variables
cached_data = None
last_cache_update = 0
cache_lock = Lock()
cache_expiry_duration = 900  # 15 minutes (in seconds)

def fetch_and_cache_data(force_refresh=False):
    """
    Fetch option data with the option to force refresh (always request fresh data).
    :param force_refresh: If True, always fetch fresh data from the API.
    :return: DataFrame containing option data.
    """
    global cached_data, last_cache_update
    current_time = time.time()

    with cache_lock:
        # If forced refresh is required or cache is expired, fetch fresh data
        if force_refresh or cached_data is None or (current_time - last_cache_update) > cache_expiry_duration:
            print("Fetching fresh data from the API...")
            cached_data = fetch_option_data()  # Fetch data from the API
            last_cache_update = current_time
        else:
            print("Using cached data...")

    return cached_data
