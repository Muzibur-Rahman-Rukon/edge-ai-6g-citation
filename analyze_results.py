#!/usr/bin/env python3
"""
Statistical Analysis and Table Generator for 6G Edge AI Paper Reproduction
Authors: M. R. Rukon, R. Hoq, M. Hasnat (IEEE ICCST 2025)

Processes raw simulation logs from CSV files, computes descriptive statistics
(Mean, Std. Dev., Min, Max), performs independent t-tests, and prints formatted
tables corresponding to the paper's results.
"""

import os
import sys
import argparse
from pathlib import Path
import numpy as np
import pandas as pd
from scipy import stats


def parse_args():
    parser = argparse.ArgumentParser(
        description="Analyze simulation results and generate statistical comparison tables."
    )
    parser.add_argument(
        "--data-dir", type=str, default="./data/raw_logs",
        help="Path to directory containing CSV results (default: ./data/raw_logs)"
    )
    parser.add_argument(
        "--output-dir", type=str, default="./data/tables",
        help="Directory to export markdown tables (default: ./data/tables)"
    )
    return parser.parse_args()


def compute_descriptive_stats(df: pd.DataFrame, metrics: list) -> pd.DataFrame:
    """Computes Mean, Standard Deviation, Min, and Max for given metrics."""
    stats_list = []
    for metric_col, display_name in metrics:
        if metric_col in df.columns:
            series = df[metric_col]
            stats_list.append({
                "Metric": display_name,
                "Mean": series.mean(),
                "Std. Dev.": series.std(),
                "Min": series.min(),
                "Max": series.max()
            })
    return pd.DataFrame(stats_list)


def compute_comparative_stats(df_base: pd.DataFrame, df_edge: pd.DataFrame, metrics: list) -> pd.DataFrame:
    """Computes mean differences and p-values using independent two-sample t-tests."""
    comp_list = []
    for metric_col, display_name in metrics:
        if metric_col in df_base.columns and metric_col in df_edge.columns:
            base_vals = df_base[metric_col]
            edge_vals = df_edge[metric_col]

            base_mean = base_vals.mean()
            edge_mean = edge_vals.mean()
            diff = edge_mean - base_mean

            # Independent t-test
            _, p_val = stats.ttest_ind(base_vals, edge_vals, equal_var=False)
            p_val_str = "< 0.001" if p_val < 0.001 else f"{p_val:.3f}"

            comp_list.append({
                "Metric": display_name,
                "Baseline Mean": base_mean,
                "Edge AI Mean": edge_mean,
                "Difference": diff,
                "p-value": p_val_str
            })
    return pd.DataFrame(comp_list)


def print_markdown_table(title: str, df: pd.DataFrame):
    """Utility to print a clean markdown table in terminal."""
    print(f"\n### {title}\n")
    print(df.to_markdown(index=False, float_format="%.2f"))


def main():
    args = parse_args()
    data_dir = Path(args.data_dir)
    out_dir = Path(args.output_dir)
    out_dir.mkdir(parents=True, exist_ok=True)

    baseline_csv = data_dir / "baseline_results.csv"
    edge_ai_csv = data_dir / "edge_ai_results.csv"

    if not baseline_csv.exists() or not edge_ai_csv.exists():
        print(f"[Error] Required CSV files not found in {data_dir}.")
        print("Please run `python3 scripts/run_simulations.py` first to generate data.")
        sys.exit(1)

    df_base = pd.read_csv(baseline_csv)
    df_edge = pd.read_csv(edge_ai_csv)

    # Metric mapping: (CSV Column Name, Paper Display Name)
    metrics_map = [
        ("throughput_gbps", "Data Throughput (Gbps)"),
        ("latency_ms", "Latency (ms)"),
        ("threat_detection_rate", "Threat Detection Rate (%)"),
        ("response_time_ms", "Response Time to Threats (ms)"),
        ("data_breach_incidents", "Data Breach Incidents (count)"),
        ("anonymization_effectiveness", "Data Anonymization Effectiveness (%)"),
        ("cpu_utilization", "CPU Utilization (%)"),
        ("memory_usage_gb", "Memory Usage (GB)")
    ]

    # Table 1: Baseline Statistics
    df_t1 = compute_descriptive_stats(df_base, metrics_map)
    print_markdown_table("Table 1: Descriptive Statistics for Baseline 6G Network (N=100)", df_t1)

    # Table 2: Edge AI Statistics
    df_t2 = compute_descriptive_stats(df_edge, metrics_map)
    print_markdown_table("Table 2: Descriptive Statistics for Edge AI-Integrated 6G Network (N=100)", df_t2)

    # Table 3: Comparative Analysis
    df_t3 = compute_comparative_stats(df_base, df_edge, metrics_map)
    print_markdown_table("Table 3: Comparative Analysis of Baseline and Edge AI-Integrated 6G Networks", df_t3)

    # Save to Markdown file
    output_md_file = out_dir / "summary_tables.md"
    with open(output_md_file, "w") as f:
        f.write("# Simulation Results Analysis\n\n")
        f.write("## Table 1: Baseline 6G Network Performance\n\n")
        f.write(df_t1.to_markdown(index=False, float_format="%.2f") + "\n\n")
        f.write("## Table 2: Edge AI-Integrated 6G Network Performance\n\n")
        f.write(df_t2.to_markdown(index=False, float_format="%.2f") + "\n\n")
        f.write("## Table 3: Comparative Analysis\n\n")
        f.write(df_t3.to_markdown(index=False, float_format="%.2f") + "\n")

    print(f"\n[Info] Results exported successfully to: {output_md_file}")


if __name__ == "__main__":
    main()
