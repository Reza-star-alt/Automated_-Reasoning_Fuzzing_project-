#!/usr/bin/env python3
import subprocess
import time
import os

def main():
    NUM_RUNS = 1000
    OUT_DIR = "outputs-2"
    os.makedirs(OUT_DIR, exist_ok=True)

    for i in range(1, NUM_RUNS + 1):
        # generate a high‐resolution timestamp seed so each run differs
        seed = time.time_ns()  
        outfile = os.path.join(OUT_DIR, f"cnf_{i:04d}.cnf")

        # call CNFuzz.py with this seed, capture its stdout into our file
        with open(outfile, "w") as f:
            subprocess.run(
                ["python3", "CNFuzz.py", str(seed)],
                stdout=f,
                check=True
            )

        # small pause so time_ns() advances
        time.sleep(0.0001)

    print(f"✅ Generated {NUM_RUNS} CNF files in “{OUT_DIR}/”")

if __name__ == "__main__":
    main()
