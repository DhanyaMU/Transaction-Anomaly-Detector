"""
Transaction Anomaly Data Generator
====================================
Generates realistic carrier transaction data with injected anomalies.
Simulates Amazon Relay's identity verification transactions.

Run with: python data/generate_transactions.py
"""

import pandas as pd
import numpy as np
from faker import Faker
import random
from datetime import datetime, timedelta
import os
import hashlib

fake = Faker()
random.seed(42)
np.random.seed(42)

# ============================================================
# CONFIGURATION
# ============================================================
NUM_NORMAL_TRANSACTIONS = 2000
NUM_ANOMALIES = 200  # 10% anomaly rate

TRANSACTION_TYPES = [
    "NEW_CARRIER_REGISTRATION",
    "DOCUMENT_SUBMISSION",
    "IDENTITY_VERIFICATION",
    "INSURANCE_UPDATE",
    "VEHICLE_ADDITION",
    "DRIVER_ONBOARDING",
    "AUTHORITY_RENEWAL",
    "ADDRESS_CHANGE",
    "CONTACT_UPDATE",
    "COMPLIANCE_CHECK"
]

DOCUMENT_TYPES = [
    "DRIVERS_LICENSE",
    "PASSPORT",
    "INSURANCE_CERTIFICATE",
    "COMPLIANCE_FORM",
    "VEHICLE_REGISTRATION"
]

ANOMALY_TYPES = [
    "DUPLICATE_SUBMISSION",
    "VELOCITY_SPIKE",
    "UNUSUAL_HOUR",
    "FAKE_IDENTITY",
    "ADDRESS_MISMATCH",
    "RAPID_CHANGES",
    "BULK_REGISTRATION",
    "SUSPICIOUS_PATTERN"
]

REGIONS = ["Northeast", "Southeast", "Midwest", "Southwest", "West Coast", "Northwest"]


# ============================================================
# GENERATE NORMAL TRANSACTIONS
# ============================================================
def generate_normal_transactions(n):
    """Generate legitimate carrier transactions"""
    transactions = []

    # Create a pool of carriers
    carrier_pool = []
    for i in range(200):
        carrier_pool.append({
            "carrier_id": f"CR-{i+1:04d}",
            "carrier_name": fake.company() + random.choice([" Trucking", " Logistics", " Transport", " Freight"]),
            "email": fake.email(),
            "phone": fake.phone_number(),
            "region": random.choice(REGIONS),
            "state": fake.state_abbr()
        })

    for i in range(n):
        carrier = random.choice(carrier_pool)

        # Normal business hours (7 AM - 8 PM), weekdays mostly
        base_date = fake.date_time_between(start_date="-90d", end_date="now")
        hour = random.choices(
            range(24),
            weights=[1,1,1,1,1,2,3,8,10,10,10,9,8,9,10,10,9,8,7,5,3,2,1,1],
            k=1
        )[0]
        transaction_time = base_date.replace(hour=hour, minute=random.randint(0, 59))

        # Normal IP patterns (consistent per carrier)
        ip_base = f"{random.randint(50,200)}.{random.randint(1,255)}"
        ip_address = f"{ip_base}.{random.randint(1,255)}.{random.randint(1,255)}"

        transaction = {
            "transaction_id": f"TXN-{i+1:06d}",
            "carrier_id": carrier['carrier_id'],
            "carrier_name": carrier['carrier_name'],
            "transaction_type": random.choice(TRANSACTION_TYPES),
            "document_type": random.choice(DOCUMENT_TYPES),
            "timestamp": transaction_time.strftime("%Y-%m-%d %H:%M:%S"),
            "hour_of_day": hour,
            "day_of_week": transaction_time.strftime("%A"),
            "email": carrier['email'],
            "phone": carrier['phone'],
            "ip_address": ip_address,
            "region": carrier['region'],
            "state": carrier['state'],
            "amount": round(random.uniform(0, 500), 2) if random.random() > 0.5 else 0,
            "session_duration_seconds": random.randint(60, 1800),
            "pages_visited": random.randint(2, 15),
            "failed_attempts": random.choices([0, 0, 0, 0, 1, 1, 2], k=1)[0],
            "device_type": random.choices(["Desktop", "Mobile", "Tablet"], weights=[60, 30, 10], k=1)[0],
            "browser": random.choice(["Chrome", "Firefox", "Safari", "Edge"]),
            "is_anomaly": False,
            "anomaly_type": "NONE",
            "risk_score": round(random.uniform(0, 30), 1)  # Low risk for normal
        }
        transactions.append(transaction)

    return transactions


# ============================================================
# GENERATE ANOMALOUS TRANSACTIONS
# ============================================================
def generate_anomalies(n):
    """Generate suspicious/fraudulent transactions"""
    anomalies = []

    for i in range(n):
        anomaly_type = random.choice(ANOMALY_TYPES)
        base_date = fake.date_time_between(start_date="-90d", end_date="now")

        # Base transaction
        transaction = {
            "transaction_id": f"TXN-A{i+1:05d}",
            "carrier_id": f"CR-{random.randint(1, 200):04d}",
            "carrier_name": fake.company() + " Trucking",
            "transaction_type": random.choice(TRANSACTION_TYPES),
            "document_type": random.choice(DOCUMENT_TYPES),
            "region": random.choice(REGIONS),
            "state": fake.state_abbr(),
            "is_anomaly": True,
            "anomaly_type": anomaly_type
        }

        # Customize based on anomaly type
        if anomaly_type == "DUPLICATE_SUBMISSION":
            # Same document submitted multiple times in short period
            hour = random.randint(8, 18)
            transaction.update({
                "timestamp": base_date.replace(hour=hour).strftime("%Y-%m-%d %H:%M:%S"),
                "hour_of_day": hour,
                "day_of_week": base_date.strftime("%A"),
                "email": fake.email(),
                "phone": fake.phone_number(),
                "ip_address": f"{random.randint(50,200)}.{random.randint(1,255)}.{random.randint(1,255)}.{random.randint(1,255)}",
                "amount": 0,
                "session_duration_seconds": random.randint(5, 30),  # Very short sessions
                "pages_visited": random.randint(1, 3),
                "failed_attempts": random.randint(0, 2),
                "device_type": "Desktop",
                "browser": "Chrome",
                "risk_score": round(random.uniform(60, 85), 1)
            })

        elif anomaly_type == "VELOCITY_SPIKE":
            # Too many transactions in short time
            hour = random.randint(0, 23)
            transaction.update({
                "timestamp": base_date.replace(hour=hour).strftime("%Y-%m-%d %H:%M:%S"),
                "hour_of_day": hour,
                "day_of_week": base_date.strftime("%A"),
                "email": fake.email(),
                "phone": fake.phone_number(),
                "ip_address": f"{random.randint(50,200)}.{random.randint(1,255)}.{random.randint(1,255)}.{random.randint(1,255)}",
                "amount": round(random.uniform(100, 1000), 2),
                "session_duration_seconds": random.randint(3, 15),  # Extremely short
                "pages_visited": random.randint(1, 2),
                "failed_attempts": random.randint(2, 5),
                "device_type": random.choice(["Desktop", "Mobile"]),
                "browser": "Chrome",
                "risk_score": round(random.uniform(70, 95), 1)
            })

        elif anomaly_type == "UNUSUAL_HOUR":
            # Transactions at 2-5 AM
            hour = random.randint(1, 5)
            transaction.update({
                "timestamp": base_date.replace(hour=hour).strftime("%Y-%m-%d %H:%M:%S"),
                "hour_of_day": hour,
                "day_of_week": base_date.strftime("%A"),
                "email": fake.email(),
                "phone": fake.phone_number(),
                "ip_address": f"{random.randint(50,200)}.{random.randint(1,255)}.{random.randint(1,255)}.{random.randint(1,255)}",
                "amount": round(random.uniform(0, 300), 2),
                "session_duration_seconds": random.randint(30, 300),
                "pages_visited": random.randint(2, 8),
                "failed_attempts": random.randint(0, 3),
                "device_type": "Mobile",
                "browser": random.choice(["Chrome", "Firefox"]),
                "risk_score": round(random.uniform(50, 75), 1)
            })

        elif anomaly_type == "FAKE_IDENTITY":
            # Suspicious identity patterns
            hour = random.randint(8, 20)
            fake_phone = f"555-{random.randint(100,999)}-{random.randint(1000,9999)}"
            transaction.update({
                "timestamp": base_date.replace(hour=hour).strftime("%Y-%m-%d %H:%M:%S"),
                "hour_of_day": hour,
                "day_of_week": base_date.strftime("%A"),
                "email": f"temp{random.randint(1000,9999)}@tempmail.com",
                "phone": fake_phone,
                "ip_address": f"10.{random.randint(1,255)}.{random.randint(1,255)}.{random.randint(1,255)}",
                "amount": 0,
                "session_duration_seconds": random.randint(60, 600),
                "pages_visited": random.randint(3, 10),
                "failed_attempts": random.randint(1, 4),
                "device_type": "Desktop",
                "browser": "Chrome",
                "risk_score": round(random.uniform(75, 95), 1)
            })

        elif anomaly_type == "ADDRESS_MISMATCH":
            # Different regions in short time
            hour = random.randint(8, 18)
            transaction.update({
                "timestamp": base_date.replace(hour=hour).strftime("%Y-%m-%d %H:%M:%S"),
                "hour_of_day": hour,
                "day_of_week": base_date.strftime("%A"),
                "email": fake.email(),
                "phone": fake.phone_number(),
                "ip_address": f"{random.randint(50,200)}.{random.randint(1,255)}.{random.randint(1,255)}.{random.randint(1,255)}",
                "amount": 0,
                "session_duration_seconds": random.randint(30, 200),
                "pages_visited": random.randint(2, 6),
                "failed_attempts": random.randint(0, 2),
                "device_type": "Desktop",
                "browser": "Firefox",
                "risk_score": round(random.uniform(55, 80), 1)
            })

        elif anomaly_type == "RAPID_CHANGES":
            # Multiple profile changes in short time
            hour = random.randint(8, 22)
            transaction.update({
                "transaction_type": random.choice(["ADDRESS_CHANGE", "CONTACT_UPDATE", "INSURANCE_UPDATE"]),
                "timestamp": base_date.replace(hour=hour).strftime("%Y-%m-%d %H:%M:%S"),
                "hour_of_day": hour,
                "day_of_week": base_date.strftime("%A"),
                "email": fake.email(),
                "phone": fake.phone_number(),
                "ip_address": f"{random.randint(50,200)}.{random.randint(1,255)}.{random.randint(1,255)}.{random.randint(1,255)}",
                "amount": 0,
                "session_duration_seconds": random.randint(10, 60),
                "pages_visited": random.randint(1, 4),
                "failed_attempts": random.randint(0, 1),
                "device_type": "Desktop",
                "browser": "Chrome",
                "risk_score": round(random.uniform(60, 85), 1)
            })

        elif anomaly_type == "BULK_REGISTRATION":
            # Many new registrations from same IP
            hour = random.randint(10, 16)
            shared_ip = f"192.168.{random.randint(1,10)}.{random.randint(1,255)}"
            transaction.update({
                "transaction_type": "NEW_CARRIER_REGISTRATION",
                "timestamp": base_date.replace(hour=hour).strftime("%Y-%m-%d %H:%M:%S"),
                "hour_of_day": hour,
                "day_of_week": base_date.strftime("%A"),
                "email": f"carrier{random.randint(1,999)}@bulkmail.com",
                "phone": f"800-{random.randint(100,999)}-{random.randint(1000,9999)}",
                "ip_address": shared_ip,
                "amount": round(random.uniform(200, 500), 2),
                "session_duration_seconds": random.randint(30, 120),
                "pages_visited": random.randint(3, 7),
                "failed_attempts": random.randint(0, 2),
                "device_type": "Desktop",
                "browser": "Chrome",
                "risk_score": round(random.uniform(65, 90), 1)
            })

        else:  # SUSPICIOUS_PATTERN
            hour = random.randint(0, 23)
            transaction.update({
                "timestamp": base_date.replace(hour=hour).strftime("%Y-%m-%d %H:%M:%S"),
                "hour_of_day": hour,
                "day_of_week": base_date.strftime("%A"),
                "email": fake.email(),
                "phone": fake.phone_number(),
                "ip_address": f"{random.randint(50,200)}.{random.randint(1,255)}.{random.randint(1,255)}.{random.randint(1,255)}",
                "amount": round(random.uniform(0, 2000), 2),
                "session_duration_seconds": random.randint(5, 2000),
                "pages_visited": random.randint(1, 30),
                "failed_attempts": random.randint(0, 5),
                "device_type": random.choice(["Desktop", "Mobile", "Tablet"]),
                "browser": random.choice(["Chrome", "Firefox", "Safari", "Edge"]),
                "risk_score": round(random.uniform(50, 95), 1)
            })

        anomalies.append(transaction)

    return anomalies


# ============================================================
# MAIN EXECUTION
# ============================================================
if __name__ == "__main__":
    print("\n" + "=" * 50)
    print("  TRANSACTION ANOMALY DATA GENERATOR")
    print("=" * 50)

    # Generate data
    print("\n[1/3] Generating normal transactions...")
    normal = generate_normal_transactions(NUM_NORMAL_TRANSACTIONS)
    print(f"      Created {len(normal)} normal transactions")

    print("[2/3] Generating anomalous transactions...")
    anomalies = generate_anomalies(NUM_ANOMALIES)
    print(f"      Created {len(anomalies)} anomalous transactions")

    print("[3/3] Combining and saving...")

    # Combine and shuffle
    all_transactions = normal + anomalies
    random.shuffle(all_transactions)

    # Create DataFrame
    df = pd.DataFrame(all_transactions)
    df = df.sort_values('timestamp').reset_index(drop=True)

    # Save
    os.makedirs("data", exist_ok=True)
    df.to_csv("data/transactions.csv", index=False)

    # Summary
    print(f"\n      Saved: data/transactions.csv")
    print("\n" + "=" * 50)
    print("  SUMMARY")
    print("=" * 50)
    print(f"\n  Total Transactions:    {len(df)}")
    print(f"  Normal:                {len(df[df['is_anomaly']==False])}")
    print(f"  Anomalous:             {len(df[df['is_anomaly']==True])}")
    print(f"  Anomaly Rate:          {len(df[df['is_anomaly']==True])/len(df)*100:.1f}%")
    print(f"\n  Anomaly Breakdown:")
    for atype in df[df['is_anomaly']==True]['anomaly_type'].value_counts().items():
        print(f"    - {atype[0]:<25} {atype[1]}")
    print(f"\n  Date Range: {df['timestamp'].min()} to {df['timestamp'].max()}")
    print("\n  DONE!")
    print("=" * 50)
