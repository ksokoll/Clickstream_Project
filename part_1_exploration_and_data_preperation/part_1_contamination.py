#import kagglehub
import pandas as pd
import os
import numpy as np

print("Load data...")
# Path setup - kagglehub download only needed on first run
#path = kagglehub.dataset_download("retailrocket/ecommerce-dataset") <- only for first time load
path = 'C://Users//Kevin//.cache//kagglehub//datasets//retailrocket//ecommerce-dataset//versions//2'
csv_files = [f for f in os.listdir(path) if f.endswith('.csv')]
print("Found files:", csv_files)
path = path + "/" + "events.csv"
df = pd.read_csv(path, sep=',')
print("Loading Data complete.")

print("General df Shape:")
print(df.shape)
# Import successful.
#print(df.info)

# Next steps: Assign device, browser, OS to each visitor
# Goal: Map every unique visitor to a realistic device/browser/OS combination

print("Getting unique visitors list...")
import numpy as np
import pandas as pd

# Get all unique visitors from the dataset
unique_visitors = df['visitorid'].unique()

# Initialize lists to store assignments
devices_list = []
browsers_list = []
os_list = []

# Assign attributes to each visitor
for visitor in unique_visitors:
    # 1. Assign device (45% desktop, 50% mobile, 5% tablet)
    device = np.random.choice(
        ['desktop', 'mobile', 'tablet'],
        p=[0.45, 0.50, 0.05]
    )
    
    # 2. Assign browser + OS based on device (conditional logic)
    if device == 'mobile':
        # Mobile: 60% iOS, 40% Android
        if np.random.random() < 0.60:  # iOS
            browser = 'safari'
            os = 'ios'
        else:  # Android
            browser = 'chrome'
            os = 'android'
    
    elif device == 'desktop':
        # Desktop browser distribution
        browser = np.random.choice(
            ['chrome', 'safari', 'edge', 'firefox'],
            p=[0.65, 0.15, 0.10, 0.10]
        )
        
        # OS depends on browser
        if browser == 'safari':
            os = 'macos'
        elif browser == 'edge':
            os = 'windows'
        else:  # Chrome/Firefox can run on multiple OS
            os = np.random.choice(
                ['windows', 'macos', 'linux'],
                p=[0.75, 0.20, 0.05]
            )
    
    else:  # tablet
        # Tablets: mostly iOS (iPad) or Android
        if np.random.random() < 0.70:  # iPad
            browser = 'safari'
            os = 'ios'
        else:  # Android Tablet
            browser = 'chrome'
            os = 'android'
    
    # Store assignments
    devices_list.append(device)
    browsers_list.append(browser)
    os_list.append(os)

# Create mapping DataFrame
visitor_attributes = pd.DataFrame({
    'visitorid': unique_visitors,
    'device': devices_list,
    'browser': browsers_list,
    'os': os_list
})

# Merge with original events
df_enriched = df.merge(visitor_attributes, on='visitorid', how='left')

# Sanity Check #1: Verify structure
print(f"Head&Tail of 'df_enriched':\n {df_enriched}")

# Sanity Check #2: Verify visitor consistency
print(df_enriched[df_enriched['visitorid'] == 257597])
# Works! User '257597' has consistent device, browser, and OS across all events.
# Note: In reality, users might have multiple devices (phone + laptop).
# For simplicity, we assign one device per visitor.

# Add human-readable timestamp column
df_enriched['timestamp_readable'] = pd.to_datetime(df_enriched['timestamp'], unit='ms')

print("------------\n\n\n")
# Next: Explore event types for contamination strategy
print(f"Unique events in 'df_enriched': \n {df['event'].unique()}")
# Only three event types: "view", "addtocart", "transaction"

# Save intermediate result
df_enriched.to_csv('df_enriched.csv', index=False)
