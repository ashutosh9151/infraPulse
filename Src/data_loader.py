"""
Data loading and simple analytics for InfraPulse.
"""

import pandas as pd
from pathlib import Path
from typing import Dict, List, Tuple
import numpy as np

DATA_DIR = Path(__file__).parent.parent / "data"


class DataStore:
    def __init__(self):
        self.requests = pd.read_csv(DATA_DIR / "citizen_requests.csv")
        self.demographics = pd.read_csv(DATA_DIR / "demographics.csv")
        self.infra = pd.read_csv(DATA_DIR / "infrastructure_indices.csv")
        self.schemes = pd.read_csv(DATA_DIR / "investment_plans.csv")

        # Normalize
        self.requests["timestamp"] = pd.to_datetime(self.requests["timestamp"])

    def get_all_requests(self) -> pd.DataFrame:
        return self.requests.copy()

    def get_district_stats(self) -> pd.DataFrame:
        """Aggregate citizen demand per district + join demographics & infra."""
        agg = (
            self.requests.groupby(["state", "district", "category"])
            .agg(
                request_count=("request_id", "count"),
                high_urgency=("urgency", lambda x: (x == "High").sum()),
            )
            .reset_index()
        )

        # Pivot categories
        pivot = agg.pivot_table(
            index=["state", "district"],
            columns="category",
            values="request_count",
            fill_value=0,
        ).reset_index()

        total = (
            self.requests.groupby(["state", "district"])
            .agg(
                total_requests=("request_id", "count"),
                high_urgency_count=("urgency", lambda x: (x == "High").sum()),
            )
            .reset_index()
        )

        # Top category
        cat_counts = (
            self.requests.groupby(["state", "district", "category"])
            .size()
            .reset_index(name="cnt")
        )
        top_cat = cat_counts.loc[
            cat_counts.groupby(["state", "district"])["cnt"].idxmax()
        ][["state", "district", "category"]].rename(columns={"category": "top_category"})

        merged = total.merge(top_cat, on=["state", "district"], how="left")
        merged = merged.merge(self.demographics, on=["state", "district"], how="left")
        merged = merged.merge(self.infra, on=["state", "district"], how="left")

        # Simple demand score
        merged["demand_score"] = (
            merged["total_requests"] * 10
            + merged["high_urgency_count"] * 15
            + merged["infra_gap_score"].fillna(50) * 0.6
            + merged["poverty_rate"].fillna(25) * 0.8
        )
        merged = merged.sort_values("demand_score", ascending=False)
        return merged

    def get_hotspots(self, top_n: int = 8) -> pd.DataFrame:
        return self.get_district_stats().head(top_n)

    def get_schemes_for_category(self, category: str) -> List[str]:
        mask = self.schemes["category"].str.contains(category, case=False, na=False)
        return self.schemes.loc[mask, "scheme_name"].tolist()

    def add_request(self, row: Dict) -> None:
        """Append a new citizen request (in-memory for demo)."""
        new_df = pd.DataFrame([row])
        self.requests = pd.concat([self.requests, new_df], ignore_index=True)

