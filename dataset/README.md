# Dataset

This project uses **ISCX VPN-NonVPN 2016** from the Canadian Institute for Cybersecurity, University of New Brunswick:
https://www.unb.ca/cic/datasets/vpn.html

The dataset is not redistributed here. Download it and place the consolidated CSV of the time-related flow features at:

```
dataset/consolidated_traffic_data.csv
```

- 59,706 complete flow records with no null values.
- 23 numerical features per record:
  - duration;
  - forward, backward and bidirectional inter-arrival time statistics;
  - active-period and idle-period statistics;
  - `flowPktsPerSecond` and `flowBytesPerSecond`.
- A `traffic_type` column holding the 14 original labels, which `src/train_model.py` maps to five classes.

Reference: G. Draper-Gil, A. H. Lashkari, M. S. I. Mamun and A. A. Ghorbani, "Characterization of Encrypted and VPN Traffic Using Time-Related Features", ICISSP 2016.
