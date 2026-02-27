# A Competition-Aware Approach to Accurate TV Show Recommendation (IEEE ICDE-23)

This repository contains the implementation of the competition-aware TV show recommendation framework proposed in "A Competition-Aware Approach to Accurate TV Show Recommendation [IEEE ICDE 2023]."

## Notice
This repository does **NOT** include the BPR-MF implementation.
It assumes that predicted preference scores from an external BPR-MF model are already generated.
This project focuses on:
- Constructing competition-aware preference representations
- Post-processing predicted scores
- Performing recommendations and evaluations

## Environment
- Python 3.10
- numpy==1.23.5
- pandas==1.3.5
- pip==26.0.1

## Execution
### Step 1. Build Matrices based on Watchable Intervals
```
run python main.py --mode 0 --method Prop --CV 1
```
- Reads raw watch log data
- Constructs preference and confidence matrices
- Exports formatted matrices for external MF training

### Step 2. Recommendation & Evaluation
This step is used to predict preference scores after running [external BPR-MF](./tvshow_rs/BPR-MF/).
```
run python main.py --mode 1 --method Prop --CV 1
```
- Loads precomputed predicted preference scores
- Adjusts preference scores by considering time factors
- Computes evaluation metrics (e.g., recall)
