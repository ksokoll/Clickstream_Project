import pandas as pd
import os
import numpy as np

path = 'C://Users//Kevin//OneDrive//Dokumente//Repositories//Clickstream_Analysis//df_enriched.csv'
df_enriched = pd.read_csv(path, sep=',')

print(f"Checking transactions of affected user beforehand:\n{df_enriched[df_enriched['visitorid'] == 1406708]}")
# The user 1406708 which fits into the below bug mask has indeed a transaction with id 937.0

# 1. Find all transactions which are relevant
df_enriched['timestamp_readable'] = pd.to_datetime(df_enriched['timestamp_readable'])
max_date = df_enriched['timestamp_readable'].max()
bug_start_date = max_date - pd.Timedelta(days=14)

# 2. create boolean bug mask
bug_mask = (
    (df_enriched['timestamp_readable'] >= bug_start_date) &
    (df_enriched['device'] == 'mobile') &
    (df_enriched['browser'] == 'safari') & 
    (df_enriched['os'] == 'ios') &         
    (df_enriched['event'] == 'transaction')
)

print(f"Total transactions in bug period :\n {bug_mask.sum()}")
# We found 572 iOS + Safari transactions

# 3. choose 80% of them by random sample
affected_indices = df_enriched[bug_mask].sample(frac=0.8).index

print(f"Transactions to contaminate: {len(affected_indices)}")
# -> 458 of them are now marked for contamination

# 4. contaminate rows 
df_enriched.loc[affected_indices, 'event'] = 'addtocart'  # Ändere Event
df_enriched.loc[affected_indices, 'transactionid'] = np.nan  # Lösche Transaction ID
# 458 'transactions' changed to 'addToCart'

print("Contamination complete!")


print(f"\nQuick sanity check: Example contaminated visitor: 1406708")
print(df_enriched[df_enriched['visitorid'] == 1406708])
# The user 1406708 is now missing the transaction as expected.

df_enriched.to_csv('df_contaminated.csv', index=False)
