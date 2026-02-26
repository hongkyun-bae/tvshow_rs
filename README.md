# A Competition-Aware Approach to Accurate TV Show Recommendation (IEEE ICDE-23)

This repository contains the implementation of the competition-aware TV show recommendation framework proposed in "A Competition-Aware Approach to Accurate TV Show Recommendation [IEEE ICDE 2023]."

## Important Notice
This repository does NOT include the BPR-MF implementation.
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
