import subprocess
import os
import csv
import time
solver = 'ilingeling'
# Configuration
folder_path = "/Users/ahmadziada/Desktop/FuzzingProject/cnf"
cadical_path = "/Users/ahmadziada/Desktop/FuzzingProject/solvers/lingeling-master/ilingeling"  # update this path
output_csv = f"/Users/ahmadziada/Desktop/FuzzingProject/prelim res/{solver}_results.csv"
timeout_seconds = 20

def run_cadical_on_formula(formula_path):
    try:
        start = time.time()
        result = subprocess.run(
            [cadical_path, formula_path],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            timeout=timeout_seconds,
            universal_newlines=True
        )
        end = time.time()
        duration = end - start

        output = result.stdout + result.stderr

        if "s UNSATISFIABLE" in output:
            return "UNSAT", None, duration
        elif "s SATISFIABLE" in output:
            # Extract lines that begin with 'v', which contain the assignment
            assignment_lines = [line for line in output.splitlines() if line.startswith("v")]
            assignment = " ".join(assignment_lines).replace("v ", "")  # Strip the 'v's
            return "SAT", assignment.strip(), duration
        else:
            return "UNKNOWN", None, duration

    except subprocess.TimeoutExpired:
        return "TIMEOUT", None, timeout_seconds
    except Exception as e:
        return "CRASH", str(e), 0

# Write results to CSV
with open(output_csv, "w", newline="") as csvfile:
    writer = csv.writer(csvfile)
    writer.writerow(["Solver", "Formula", "Result", "Time (s)", "Assignment"])

    for filename in os.listdir(folder_path):
        if filename.endswith(".cnf"):
            formula_path = os.path.join(folder_path, filename)
            result, assignment, duration = run_cadical_on_formula(formula_path)
            writer.writerow(["CaDiCaL", filename, result, f"{duration:.2f}", assignment or ""])
            print(f"{filename}: {result} in {duration:.2f}s")
