"""
Quick JSON output test script - passes --json flag automatically
Usage: python test_json.py [sample_number]
"""
import sys
import subprocess

# Get sample number from args, default to 1
sample_num = sys.argv[1] if len(sys.argv) > 1 else "1"

# Run test with JSON flag
subprocess.run([sys.executable, "tests/test_with_samples.py", sample_num, "--json"])
