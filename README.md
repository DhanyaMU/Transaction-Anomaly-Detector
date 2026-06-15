# Transaction Anomaly Detector

## Overview
A machine learning-powered system that detects suspicious and fraudulent patterns in carrier transactions for Amazon Relay's identity verification pipeline. Uses **Isolation Forest ML model** combined with rule-based detection to identify fraud, duplicate submissions, fake identities, and unusual behavioral patterns in real-time.

## Problem Statement
Amazon Relay processes millions of carrier transactions annually. Fraudulent actors attempt to:
- Register fake carrier accounts
- Submit duplicate or forged documents
- Take over legitimate accounts
- Exploit the system through bulk automated registrations

This project detects these threats automatically with 90%+ accuracy.

## Features

| Feature | Description |
|---------|-------------|
| ML Anomaly Detection | Isolation Forest model trained on transaction behavior |
| Rule-Based Detection | Threshold-based flagging for known fraud patterns |
| Dual Engine | Combines ML + Rules for maximum coverage |
| Real-Time Dashboard | Interactive Streamlit dashboard with live metrics |
| Model Performance | Precision, Recall, F1 Score, Confusion Matrix |
| Investigation Panel | Click any flagged transaction for full details + recommended action |
| Hourly Pattern Analysis | Identifies suspicious time-of-day patterns |
| Regional Analysis | Compares anomaly rates across regions |
| Risk Scoring | 0-100 risk score for every transaction |

## Anomaly Types Detected

| Anomaly Type | Description | Risk Level |
|-------------|-------------|-----------|
| DUPLICATE_SUBMISSION | Same document submitted multiple times | High |
| VELOCITY_SPIKE | Too many transactions in short time | High |
| UNUSUAL_HOUR | Transactions at 1-5 AM | Medium |
| FAKE_IDENTITY | Suspicious email/phone patterns (temp emails, 555 numbers) | Critical |
| ADDRESS_MISMATCH | Location inconsistencies | Medium |
| RAPID_CHANGES | Multiple profile changes in short time | High |
| BULK_REGISTRATION | Many registrations from same IP | Critical |
| SUSPICIOUS_PATTERN | General behavioral anomaly detected by ML | Medium |

## Tech Stack

- **Frontend:** Streamlit
- **ML Model:** Isolation Forest (Scikit-Learn)
- **Visualization:** Plotly (interactive charts)
- **Data Processing:** Pandas, NumPy
- **Data Generation:** Faker
