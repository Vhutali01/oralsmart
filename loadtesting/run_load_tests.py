#!/usr/bin/env python3
"""
Simple Load Testing Launcher for OralSmart
==========================================

A user-friendly wrapper for running enhanced load tests with different presets.
"""

import sys
import subprocess
from pathlib import Path

def run_command(cmd):
    """Run a command and return success status"""
    try:
        result = subprocess.run(cmd, shell=True, check=True)
        return result.returncode == 0
    except subprocess.CalledProcessError as e:
        print(f"Error running command: {e}")
        return False

def main():
    script_dir = Path(__file__).parent
    enhanced_script = script_dir / "enhanced_load_test.py"
    
    print("🚀 OralSmart Load Testing Launcher")
    print("=" * 40)
    
    if len(sys.argv) > 1:
        # Handle command line arguments
        if sys.argv[1] == "--help" or sys.argv[1] == "-h":
            print("Available options:")
            print("  quick     - Quick test (2 iterations, light+moderate scenarios)")
            print("  full      - Full test (3 iterations, all scenarios)")
            print("  stress    - Stress test (3 iterations, heavy scenario only)")
            print("  dev       - Development test (1 iteration, light scenario)")
            print("  custom    - Pass custom arguments to enhanced_load_test.py")
            return 0
        
        preset = sys.argv[1]
    else:
        # Interactive mode
        print("Choose a testing preset:")
        print("1. Super Quick Test (30 seconds per test, 1 iteration)")
        print("2. Quick Test (2 iterations, light + moderate load)")
        print("3. Full Test (3 iterations, all scenarios)")  
        print("4. Stress Test (3 iterations, heavy load only)")
        print("5. Development Test (1 iteration, light load only)")
        print("6. Custom (specify your own parameters)")
        
        choice = input("\nEnter your choice (1-6): ").strip()
        
        preset_map = {
            "1": "super_quick",
            "2": "quick",
            "3": "full", 
            "4": "stress",
            "5": "dev",
            "6": "custom"
        }
        
        preset = preset_map.get(choice)
        if not preset:
            print("Invalid choice!")
            return 1
    
    # Define preset commands
    presets = {
        "super_quick": f"python {enhanced_script} --iterations=1 --scenarios quick_test --check-server",
        "quick": f"python {enhanced_script} --iterations=2 --scenarios light_load moderate_load --check-server",
        "full": f"python {enhanced_script} --iterations=3 --check-server",
        "stress": f"python {enhanced_script} --iterations=3 --scenarios heavy_load --check-server",
        "dev": f"python {enhanced_script} --iterations=1 --scenarios light_load --check-server"
    }
    
    if preset == "custom":
        print("\nCustom mode - enter your parameters:")
        iterations = input("Number of iterations (default: 3): ").strip() or "3"
        
        print("Available scenarios: light_load, moderate_load, heavy_load")
        scenarios = input("Scenarios (space-separated, default: all): ").strip()
        
        host = input("Target host (default: http://localhost:8000): ").strip() or "http://localhost:8000"
        
        cmd = f"python {enhanced_script} --iterations={iterations} --host={host} --check-server"
        if scenarios:
            cmd += f" --scenarios {scenarios}"
    else:
        cmd = presets[preset]
        print(f"\n🔧 Running preset: {preset}")
        print(f"Command: {cmd}")
    
    print(f"\n⏳ Starting load test...")
    print("Note: This may take several minutes depending on the preset chosen.")
    
    # Run the command
    success = run_command(cmd)
    
    if success:
        print(f"\n✅ Load testing completed successfully!")
        print(f"📊 Check the reports/ directory for graphs and detailed results.")
    else:
        print(f"\n❌ Load testing failed. Check the error messages above.")
        return 1
    
    return 0

if __name__ == "__main__":
    exit(main())