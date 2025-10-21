#!/usr/bin/env python3
"""Helper: build scaling results from existing reports and call the plotting functions

This script finds recent virtual_users_* report directories and builds a results
list that matches the structure used by VirtualUserLoadTester.run_scaling_test,
then calls the new plotting functions to create the ResponseTime vs Users plot.
"""
import sys
from pathlib import Path
import pandas as pd

sys.path.insert(0, str(Path(__file__).parent))
from virtual_user_load_test import VirtualUserLoadTester

REPORTS_DIR = Path(__file__).parent / "reports"

def find_latest_virtual_dir():
    dirs = [d for d in REPORTS_DIR.iterdir() if d.is_dir() and d.name.startswith('virtual_users_')]
    if not dirs:
        return None
    return sorted(dirs, key=lambda d: d.stat().st_mtime)[-1]


def build_results_from_dir(d):
    """Scan a virtual_users directory and return a list of result dicts with user_count and iteration"""
    results = []
    for f in d.iterdir():
        name = f.name
        # Look for files ending with _stats.csv
        if name.endswith('_stats.csv') and 'Patient_management_workflow' in name:
            # Example filename: Patient_management_workflow_5users_iter1_stats.csv
            parts = name.split('_')
            try:
                # last parts are like '5users', 'iter1', 'stats.csv'
                user_part = parts[-4] if parts[-1].endswith('.csv') else parts[-3]
            except Exception:
                # fallback parse
                tokens = name.replace('.csv','').split('_')
                try:
                    user_part = [t for t in tokens if t.endswith('users')][0]
                except Exception:
                    continue

            try:
                user_count = int(user_part.replace('users',''))
            except Exception:
                # try alternative
                import re
                m = re.search(r"(\d+)users", name)
                if m:
                    user_count = int(m.group(1))
                else:
                    continue

            import re
            m2 = re.search(r"iter(\d+)", name)
            if not m2:
                continue
            iteration = int(m2.group(1))

            # Use pandas to parse the CSV similar to parse_csv_stats
            try:
                df = pd.read_csv(f)
            except Exception:
                continue

            # Find aggregated row
            agg = df[df['Name'] == 'Aggregated']
            if agg.empty:
                pot = df[df['Name'].isna() | (df['Name'] == '')]
                if not pot.empty:
                    agg = pot.iloc[-1:]

            if not agg.empty:
                row = agg.iloc[0]
                stats = {
                    'load_time': float(row['Average Response Time']),
                    'latency': float(row['95%']),
                    'connect_time': float(row['Min Response Time']),
                    'requests_per_second': float(row['Requests/s']),
                    'failure_rate': (float(row['Failure Count']) / float(row['Request Count']) * 100) if float(row['Request Count'])>0 else 0,
                    'total_requests': int(row['Request Count']),
                    'iteration': iteration,
                    'user_count': user_count
                }
                results.append(stats)

    return results


def main():
    d = find_latest_virtual_dir()
    if not d:
        print('No virtual_users reports found')
        return 1
    print('Using directory:', d)
    results = build_results_from_dir(d)
    if not results:
        print('No results parsed from CSVs in', d)
        return 1

    tester = VirtualUserLoadTester()
    tester.reports_dir = d  # save outputs next to these
    tester.create_response_time_vs_users_plot('Patient management workflow', results)
    print('Done')
    return 0

if __name__ == "__main__":
    exit(main())