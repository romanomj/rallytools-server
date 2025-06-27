import numpy as np
from sklearn.cluster import DBSCAN
from collections import defaultdict
import matplotlib.pyplot as plt
import pandas as pd

def analyze_market_data(data):
    """
    Analyzes a list of market data to calculate metrics for each unique item.

    This function groups items by their ID and calculates the minimum price,
    maximum price, total quantity, and a market price for each item. The market
    price is determined by finding the lowest-priced cluster of listings.

    Args:
        data (list): A list of dictionaries, where each dictionary represents
                     a market listing with 'item', 'unit_price', and 'quantity'.

    Returns:
        dict: A dictionary where keys are item IDs and values are another
              dictionary containing the calculated metrics: 'min_price',
              'max_price', 'market_price', 'total_quantity'.
    """
    # Group listings by item ID
    grouped_by_item = defaultdict(list)
    for listing in data:
        item_id = listing.get('item', {}).get('id')
        if item_id:
            grouped_by_item[item_id].append(listing)

    # Dictionary to hold the final results
    market_analysis = {}

    # Process each group of items
    for item_id, listings in grouped_by_item.items():
        prices = [d['unit_price'] for d in listings]
        quantities = [d['quantity'] for d in listings]
        total_quantity = sum(quantities)

        min_price = min(prices)
        max_price = max(prices)
        
        market_price = calculate_market_price(prices)

        market_analysis[item_id] = {
            'min_price': min_price,
            'max_price': max_price,
            'market_price': market_price,
            'total_quantity': total_quantity,
        }

    return market_analysis

def calculate_market_price(prices):
    """
    Calculates the market price from a list of prices using clustering.

    This function uses the DBSCAN clustering algorithm to identify groups of
    similar prices. It then identifies the cluster with the lowest average
    price and returns the minimum price from that cluster as the market price.
    This helps to find a consensus price while ignoring high-priced outliers.

    Args:
        prices (list): A list of numerical prices for a single item.

    Returns:
        float: The calculated market price. Returns the overall minimum price
               if clustering doesn't yield a clear result.
    """
    if not prices:
        return 0
        
    # If there are very few listings, just return the minimum price.
    if len(prices) < 3:
        return min(prices)

    prices_array = np.array(prices).reshape(-1, 1)

    # Use DBSCAN to find clusters of prices.
    # The 'eps' parameter is crucial and may need tuning based on your data's scale.
    # It defines the maximum distance between two samples for one to be considered
    # as in the neighborhood of the other. We can set it dynamically.
    price_range = np.ptp(prices_array) # Peak-to-peak (max - min)
    # A simple heuristic for eps: 5% of the price range, with a minimum value.
    eps_value = max(price_range * 0.05, 1000) 

    db = DBSCAN(eps=eps_value, min_samples=2).fit(prices_array)
    labels = db.labels_

    # -1 represents noise/outliers in DBSCAN
    unique_labels = set(labels)
    
    if -1 in unique_labels:
      unique_labels.remove(-1)
      
    # If no clusters are found, fall back to the minimum price
    if not unique_labels:
      return min(prices)

    # Find the cluster with the lowest average price
    lowest_avg_price = float('inf')
    best_cluster_label = -1

    for label in unique_labels:
        cluster_prices = prices_array[labels == label]
        avg_price = np.mean(cluster_prices)
        if avg_price < lowest_avg_price:
            lowest_avg_price = avg_price
            best_cluster_label = label

    # The market price is the minimum price from the lowest-priced cluster
    market_price_cluster = prices_array[labels == best_cluster_label]
    return float(np.min(market_price_cluster))

# --- Data Validation ---

def _validate_data(data):
    """
    Validates the input data dictionary to ensure it has the required keys
    and that the lists are of equal length.
    """
    required_keys = ["commodity", "quantities", "market_prices"]
    for key in required_keys:
        if key not in data:
            raise ValueError(f"Missing required key in data: '{key}'")

    quantities = data["quantities"]
    prices = data["market_prices"]

    if len(quantities) != len(prices):
        raise ValueError("The 'quantities' and 'market_prices' lists must be of the same length.")

    if len(prices) == 0:
        raise ValueError("Input lists cannot be empty.")

    # Check for additional keys needed for advanced metrics
    has_ohlc = all(k in data for k in ['high_prices', 'low_prices', 'close_prices'])

    return True, has_ohlc


# --- Metric Calculation and Graphing Functions ---

def calculate_and_graph_vwap(data: dict):
    """
    Calculates and graphs the Volume Weighted Average Price (VWAP).

    VWAP is the average price of a commodity weighted by its trading volume.
    It provides a benchmark of the "true" average price for a given period.

    Args:
        data (dict): A dictionary containing 'market_prices' and 'quantities'.
    """
    try:
        _validate_data(data)
    except ValueError as e:
        print(f"Data validation error: {e}")
        return

    prices = np.array(data['market_prices'])
    volumes = np.array(data['quantities'])
    commodity_name = data['commodity'].title()

    # Calculate VWAP
    # In this context, we assume 'market_prices' represents the typical price for the period.
    cumulative_price_volume = np.cumsum(prices * volumes)
    cumulative_volume = np.cumsum(volumes)

    # Avoid division by zero if the first volume is 0
    vwap = np.full_like(prices, fill_value=np.nan)
    non_zero_mask = cumulative_volume != 0
    vwap[non_zero_mask] = cumulative_price_volume[non_zero_mask] / cumulative_volume[non_zero_mask]

    # Plotting
    plt.style.use('seaborn-v0_8-darkgrid')
    fig, ax = plt.subplots(figsize=(12, 6))

    time_periods = np.arange(len(prices))

    ax.plot(time_periods, prices, label='Market Price', color='skyblue', marker='o', linestyle='-')
    ax.plot(time_periods, vwap, label='VWAP', color='coral', marker='x', linestyle='--')

    ax.set_title(f'Market Price vs. VWAP for {commodity_name}', fontsize=16)
    ax.set_xlabel('Time Period', fontsize=12)
    ax.set_ylabel('Price', fontsize=12)
    ax.legend(fontsize=10)
    ax.grid(True, which='both', linestyle='--', linewidth=0.5)

    plt.tight_layout()
    plt.show()


def calculate_and_graph_price_volume_correlation(data: dict):
    """
    Calculates Price-Volume correlation and displays it on a scatter plot.

    This helps visualize the relationship between price movements and trading
    activity. A positive correlation means price tends to rise on higher volume.

    Args:
        data (dict): A dictionary containing 'market_prices' and 'quantities'.
    """
    try:
        _validate_data(data)
    except ValueError as e:
        print(f"Data validation error: {e}")
        return

    prices = np.array(data['market_prices'])
    volumes = np.array(data['quantities'])
    commodity_name = data['commodity'].title()

    # Calculate the Pearson correlation coefficient
    correlation_matrix = np.corrcoef(prices, volumes)
    correlation = correlation_matrix[0, 1] if correlation_matrix.shape == (2, 2) else 0

    # Plotting
    plt.style.use('seaborn-v0_8-darkgrid')
    fig, ax = plt.subplots(figsize=(10, 6))

    ax.scatter(volumes, prices, alpha=0.7, color='mediumseagreen', edgecolors='k')

    ax.set_title(f'Price vs. Volume Correlation for {commodity_name}', fontsize=16)
    ax.set_xlabel('Quantity (Volume)', fontsize=12)
    ax.set_ylabel('Market Price', fontsize=12)

    # Add correlation text to the plot
    ax.text(0.05, 0.95, f'Correlation: {correlation:.4f}',
            transform=ax.transAxes, fontsize=12,
            verticalalignment='top', bbox=dict(boxstyle='round,pad=0.5', fc='wheat', alpha=0.5))

    ax.grid(True, which='both', linestyle='--', linewidth=0.5)

    plt.tight_layout()
    plt.show()


def calculate_and_graph_money_flow_index(data: dict, period: int = 14):
    """
    Calculates and graphs the Money Flow Index (MFI).

    MFI is a momentum indicator that uses both price and volume to measure
    buying and selling pressure. It is often called the volume-weighted RSI.
    Values above 80 are considered overbought, and below 20 are oversold.

    Note: This calculation uses 'market_prices' as the 'Typical Price'
    since High and Low prices are not provided.

    Args:
        data (dict): A dictionary containing 'market_prices' and 'quantities'.
        period (int): The look-back period for the MFI calculation.
    """
    try:
        _validate_data(data)
    except ValueError as e:
        print(f"Data validation error: {e}")
        return

    prices = pd.Series(data['market_prices'])
    volumes = pd.Series(data['quantities'])
    commodity_name = data['commodity'].title()

    if len(prices) <= period:
        print(f"Error: Not enough data for the specified period of {period}. "
              f"Need at least {period + 1} data points.")
        return

    # Using market_price as the typical price
    typical_price = prices
    money_flow = typical_price * volumes

    price_diff = typical_price.diff(1)

    positive_flow = pd.Series(np.where(price_diff > 0, money_flow, 0))
    negative_flow = pd.Series(np.where(price_diff < 0, money_flow, 0))

    positive_mf = positive_flow.rolling(window=period).sum()
    negative_mf = negative_flow.rolling(window=period).sum()

    # Avoid division by zero
    money_flow_ratio = positive_mf / negative_mf
    money_flow_ratio = money_flow_ratio.replace([np.inf], 9999) # Handle cases where negative_mf is 0

    mfi = 100 - (100 / (1 + money_flow_ratio))

    # Plotting
    plt.style.use('seaborn-v0_8-darkgrid')
    fig, ax = plt.subplots(figsize=(12, 6))

    time_periods = np.arange(len(prices))

    ax.plot(time_periods, mfi, label=f'MFI ({period}-period)', color='purple')
    ax.axhline(80, linestyle='--', color='red', alpha=0.7, label='Overbought (80)')
    ax.axhline(50, linestyle='--', color='gray', alpha=0.5)
    ax.axhline(20, linestyle='--', color='green', alpha=0.7, label='Oversold (20)')

    ax.set_title(f'Money Flow Index (MFI) for {commodity_name}', fontsize=16)
    ax.set_xlabel('Time Period', fontsize=12)
    ax.set_ylabel('MFI Value', fontsize=12)
    ax.set_ylim(0, 100)
    ax.legend(fontsize=10)
    ax.grid(True, which='both', linestyle='--', linewidth=0.5)

    plt.tight_layout()
    plt.show()


def calculate_and_graph_chaikin_money_flow(data: dict, period: int = 20):
    """
    Calculates and graphs the Chaikin Money Flow (CMF).

    CMF measures the amount of Money Flow Volume over a specific period.
    It can be used to confirm trends or signal reversals. Values above zero
    indicate buying pressure, while values below zero indicate selling pressure.

    *** IMPORTANT NOTE ***
    This indicator REQUIRES High, Low, Close prices, and Volume.
    The function will not run without these keys in the input dictionary:
    'high_prices', 'low_prices', 'close_prices', 'quantities'.

    Args:
        data (dict): A dictionary containing high, low, close prices and quantities.
        period (int): The look-back period for the CMF calculation.
    """
    try:
        is_valid, has_ohlc = _validate_data(data)
        if not has_ohlc:
            print("--- Chaikin Money Flow Warning ---")
            print("Calculation skipped: This function requires 'high_prices', 'low_prices', "
                  "'close_prices', and 'quantities' in the data dictionary.")
            print("---------------------------------")
            return
    except ValueError as e:
        print(f"Data validation error: {e}")
        return

    highs = pd.Series(data['high_prices'])
    lows = pd.Series(data['low_prices'])
    closes = pd.Series(data['close_prices'])
    volumes = pd.Series(data['quantities'])
    commodity_name = data['commodity'].title()

    if len(closes) < period:
        print(f"Error: Not enough data for the specified period of {period}. "
              f"Need at least {period} data points.")
        return

    # Calculate Money Flow Multiplier and Volume
    # Handle division by zero if High == Low
    mf_multiplier = ((closes - lows) - (highs - closes)) / (highs - lows)
    mf_multiplier = mf_multiplier.fillna(0) # If High == Low, the change is 0

    mf_volume = mf_multiplier * volumes

    # Calculate Chaikin Money Flow
    cmf = mf_volume.rolling(window=period).sum() / volumes.rolling(window=period).sum()

    # Plotting
    plt.style.use('seaborn-v0_8-darkgrid')
    fig, ax = plt.subplots(figsize=(12, 6))

    time_periods = np.arange(len(closes))

    ax.plot(time_periods, cmf, label=f'CMF ({period}-period)', color='darkcyan')
    ax.axhline(0, linestyle='--', color='black', alpha=0.8)

    # Fill between CMF line and zero line for better visualization
    ax.fill_between(time_periods, cmf, 0, where=(cmf > 0), facecolor='green', alpha=0.3)
    ax.fill_between(time_periods, cmf, 0, where=(cmf < 0), facecolor='red', alpha=0.3)

    ax.set_title(f'Chaikin Money Flow (CMF) for {commodity_name}', fontsize=16)
    ax.set_xlabel('Time Period', fontsize=12)
    ax.set_ylabel('CMF Value', fontsize=12)
    ax.legend(fontsize=10)
    ax.grid(True, which='both', linestyle='--', linewidth=0.5)

    plt.tight_layout()
    plt.show()
