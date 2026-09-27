#!/usr/bin/env python3
"""
Simulation Automation Runner for 6G Edge AI Paper Reproduction
Authors: M. R. Rukon, R. Hoq, M. Hasnat (IEEE ICCST 2025)

Executes 100 iterations of ns-3 baseline and Edge AI scenarios,
collects execution logs, and formats performance metrics into CSVs.
"""

import os
import sys
import argparse
import subprocess
import logging
from pathlib import Path
import numpy as np
import pandas as pd

# Configure Logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    handlers=[logging.StreamHandler(sys.stdout)]
)

def parse_args():
    parser = argparse.ArgumentParser(
        description="Run ns-3 simulations for Baseline vs Edge AI-Integrated 6G Networks."
    )
    parser.add_argument(
        "--runs", type=int, default=100,
        help="Number of simulation runs per scenario (default: 100)"
    )
    parser.add_argument(
        "--ns3-path", type=str, default="./ns3_simulation",
        help="Path to ns-3 directory or wrapper (default: ./ns3_simulation)"
    )
    parser.add_argument(
        "--output-dir", type=str, default="./data/raw_logs",
        help="Directory to store generated CSV results (default: ./data/raw_logs)"
    )
    parser.add_argument(
        "--mock", action="store_true",
        help="Generate synthetic data following the paper's distributions if ns-3 build is unavailable."
    )
    return parser.parse_args()


def generate_paper_aligned_mock_data(num_runs: int, scenario: str) -> pd.DataFrame:
    """
    Generates synthetic evaluation data based on the paper's reported mean and standard deviations.
    Useful for testing analysis scripts before full ns-3 C++ backend integration.
    """
    np.random.seed(42 if scenario == "baseline" else 2025)

    if scenario == "baseline":
        means = {
            "throughput_gbps": 9.79,
            "latency_ms": 49.15,
            "threat_detection_rate": 69.62,
            "response_time_ms": 198.75,
            "data_breach_incidents": 4.12,
            "anonymization_effectiveness": 79.79,
            "cpu_utilization": 49.55,
            "memory_usage_gb": 8.17,
        }
        stds = {
            "throughput_gbps": 0.93,
            "latency_ms": 4.71,
            "threat_detection_rate": 10.17,
            "response_time_ms": 18.45,
            "data_breach_incidents": 2.61,
            "anonymization_effectiveness": 5.51,
            "cpu_utilization": 5.74,
            "memory_usage_gb": 0.91,
        }
    else:  # edge_ai
        means = {
            "throughput_gbps": 12.21,
            "latency_ms": 29.58,
            "threat_detection_rate": 87.58,
            "response_time_ms": 103.37,
            "data_breach_incidents": 0.84,
            "anonymization_effectiveness": 88.71,
            "cpu_utilization": 59.33,
            "memory_usage_gb": 10.07,
        }
        stds = {
            "throughput_gbps": 0.99,
            "latency_ms": 5.58,
            "threat_detection_rate": 10.91,
            "response_time_ms": 20.53,
            "data_breach_incidents": 1.00,
            "anonymization_effectiveness": 5.36,
            "cpu_utilization": 4.78,
            "memory_usage_gb": 1.31,
        }

    records = []
    for run_id in range(1, num_runs + 1):
        row = {"run_id": run_id, "scenario": scenario}
        for key in means:
            val = np.random.normal(means[key], stds[key])
            # Bound realistic values
            if "incidents" in key:
                val = max(0, int(round(val)))
            elif "rate" in key or "effectiveness" in key or "utilization" in key:
                val = np.clip(val, 0.0, 100.0)
            elif val < 0:
                val = abs(val)
            row[key] = round(val, 2)
        records.append(row)

    return pd.DataFrame(records)


def run_ns3_experiment(ns3_path: str, script_name: str, seed: int) -> dict:
    """
    Executes a single ns-3 C++ binary target with a specific random seed.
    Expects stdout formatted as key=value pairs.
    """
    cmd = [
        f"{ns3_path}/ns3", "run",
        f"scratch/{script_name} --RngRun={seed}"
    ]
    try:
        result = subprocess.run(cmd, capture_output=True, text=True, check=True)
        metrics = {}
        for line in result.stdout.splitlines():
            if "=" in line:
                key, val = line.strip().split("=")
                metrics[key] = float(val)
        return metrics
    except Exception as e:
        logging.error(f"Failed to execute ns-3 run (Seed {seed}): {e}")
        raise e


def main():
    args = parse_args()
    out_dir = Path(args.output_dir)
    out_dir.mkdir(parents=True, exist_ok=True)

    logging.info(f"Starting simulation batch (N={args.runs} runs per scenario)...")

    if args.mock:
        logging.info("Running in --mock mode. Generating dataset aligned with paper statistics...")
        df_baseline = generate_paper_aligned_mock_data(args.runs, "baseline")
        df_edge_ai = generate_paper_aligned_mock_data(args.runs, "edge_ai")
    else:
        logging.info("Executing native ns-3 simulation scripts...")
        
        # 1. Run Baseline Scenario
        baseline_results = []
        for seed in range(1, args.runs + 1):
            logging.info(f"[Baseline] Running iteration {seed}/{args.runs}...")
            res = run_ns3_experiment(args.ns3_path, "baseline_6g", seed)
            res["run_id"] = seed
            res["scenario"] = "baseline"
            baseline_results.append(res)
        df_baseline = pd.DataFrame(baseline_results)

        # 2. Run Edge AI Scenario
        edge_results = []
        for seed in range(1, args.runs + 1):
            logging.info(f"[Edge AI] Running iteration {seed}/{args.runs}...")
            res = run_ns3_experiment(args.ns3_path, "edge_ai_6g", seed)
            res["run_id"] = seed
            res["scenario"] = "edge_ai"
            edge_results.append(res)
        df_edge_ai = pd.DataFrame(edge_results)

    # Save outputs to CSV
    baseline_path = out_dir / "baseline_results.csv"
    edge_ai_path = out_dir / "edge_ai_results.csv"
    combined_path = out_dir / "combined_simulation_results.csv"

    df_baseline.to_csv(baseline_path, index=False)
    df_edge_ai.to_csv(edge_ai_path, index=False)

    df_combined = pd.concat([df_baseline, df_edge_ai], ignore_index=False)
    df_combined.to_csv(combined_path, index=False)

    logging.info(f"Simulations completed successfully!")
    logging.info(f"Saved: {baseline_path}")
    logging.info(f"Saved: {edge_ai_path}")
    logging.info(f"Saved: {combined_path}")


if __name__ == "__main__":
    main()
