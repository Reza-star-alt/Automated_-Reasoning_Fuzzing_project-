#!/usr/bin/env python3
"""
cnfuzz.py — random CNF (or QDIMACS) generator
Ported from Biere 2009–2010 C version.
"""

import sys
import os
import time
import random

MAX = 20

def pick(frm: int, to: int) -> int:
    """Return a random integer between frm and to, inclusive."""
    assert frm <= to
    return random.randint(frm, to)

def numstr(s: str) -> bool:
    """True iff s consists only of digits."""
    return s.isdigit()

def rand_sign() -> int:
    """Randomly return +1 or -1 with equal probability."""
    return -1 if pick(31, 32) == 32 else 1

def usage():
    print(
        "usage: cnfuzz.py [-h][-q][<seed>][<option-file>]\n"
        "\n"
        "  -h   print this help message\n"
        "  -q   generate quantified CNF in QDIMACS format\n"
        "\n"
        "If <seed> is omitted it’s derived from PID and time.\n"
        "Option file format (one per line): <opt> <lower> <upper> <ignored>.\n"
        "These options are 'fuzzed' and emitted as comments."
    )
    sys.exit(0)

def main():
    # --- parse command-line args ---
    qbf = False
    seed = None
    options_file = None

    args = sys.argv[1:]
    for arg in args:
        if arg == "-h":
            usage()
        elif arg == "-q":
            qbf = True
        elif numstr(arg):
            if seed is not None:
                print("*** cnfuzz: multiple seeds", file=sys.stderr)
                sys.exit(1)
            seed = int(arg)
            if seed < 0:
                print("*** cnfuzz: seed overflow", file=sys.stderr)
                sys.exit(1)
        elif options_file is not None:
            print("*** cnfuzz: multiple option files", file=sys.stderr)
            sys.exit(1)
        else:
            options_file = arg

    # --- initialize random seed ---
    if seed is None:
        seed = abs((int(time.time()) * os.getpid()) >> 1)
    random.seed(seed)
    print(f"c seed {seed}")
    sys.stdout.flush()

    # --- QBF header ---
    if qbf:
        print("c qbf")
        fp = pick(0, 3)
        if fp != 0:
            print("c but forced to be propositional")
    else:
        fp = 1  # irrelevant if not qbf

    # --- options file fuzzing ---
    if options_file:
        ospread = pick(0, 10)
        allmin = pick(0, 1)
        allmax = 0 if allmin else pick(0, 1)

        if allmin:
            print("c allmin")
        elif allmax:
            print("c allmax")
        print(f"c {ospread} ospread")

        try:
            with open(options_file) as f:
                for line in f:
                    parts = line.split()
                    if len(parts) >= 4:
                        opt_name, val_s, min_s, max_s = parts[:4]
                        val = int(val_s)
                        mn, mx = int(min_s), int(max_s)
                        if pick(0, ospread) == 0:
                            if allmin:
                                val = mn
                            elif allmax:
                                val = mx
                            else:
                                val = pick(mn, mx)
                        print(f"c --{opt_name}={val}")
        except IOError:
            print(f"*** cnfuzz: can not read '{options_file}'", file=sys.stderr)
            sys.exit(1)

    # reseed to match C’s double-srand behavior
    random.seed(seed)

    # --- high-level parameters ---
    w        = pick(10, 70)
    scramble = pick(-1, 1)
    nlayers  = pick(1, 20)
    eqs      = 0 if pick(0, 2) != 0 else pick(0, 99)
    ands     = 0 if pick(0, 1) != 0 else pick(0, 99)

    print(f"c width {w}")
    print(f"c scramble {scramble}")
    print(f"c layers {nlayers}")
    print(f"c equalities {eqs}")
    print(f"c ands {ands}")

    # --- per-layer setup ---
    low     = [0] * nlayers
    high    = [0] * nlayers
    width   = [0] * nlayers
    quant   = [0] * nlayers
    clauses = [0] * nlayers
    unused  = [None] * nlayers

    for i in range(nlayers):
        width[i] = pick(10, w)
        quant[i] = pick(-1, 1) if (qbf and fp == 0) else 0
        low[i]   = (high[i-1] + 1) if i > 0 else 1
        high[i]  = low[i] + width[i] - 1

        m = width[i] + (width[i-1] if i > 0 else 0)
        n = (pick(300, 450) * m) // 100
        clauses[i] = n

        print(
            f"c layer[{i}] = [{low[i]}..{high[i]}] "
            f"w={width[i]} v={m} c={n} "
            f"r={n/m:.2f} q={quant[i]}"
        )

        # build initial unused-literals pool
        pool = []
        for v in range(low[i], high[i] + 1):
            pool.append(-v)
            pool.append( v)
        unused[i] = pool

    # --- prepare AND-clauses arity ---
    last_m = width[-1] + (width[-2] if nlayers > 1 else 0)
    maxarity = last_m // 2
    if maxarity >= MAX:
        maxarity = MAX - 1
    arity = [ pick(2, maxarity) for _ in range(ands) ]

    # --- count total clauses & emit problem line ---
    total_clauses = sum(a + 1 for a in arity)       # from AND-gates
    total_clauses += sum(clauses)                   # regular clauses
    total_clauses += 2 * eqs                        # equality pairs
    m_vars = high[-1]
    print(f"p cnf {m_vars} {total_clauses}")

    # --- QDIMACS quantifier lines ---
    if qbf and fp == 0:
        for i in range(nlayers):
            if i == 0 and quant[0] == 0:
                continue
            prefix = 'a' if quant[i] < 0 else 'e'
            vs = " ".join(str(v) for v in range(low[i], high[i] + 1))
            print(f"{prefix} {vs} 0")

    # --- clause generation state ---
    mark = [False] * (m_vars + 1)

    # --- generate random CNF clauses per layer ---
    for i in range(nlayers):
        for _ in range(clauses[i]):
            # decide clause length ℓ ≥ 3
            l = 3
            while l < MAX and pick(17, 19) != 17:
                l += 1

            lits = []
            for _ in range(l):
                # possibly “drift” up to outer layers
                layer = i
                while layer > 0 and pick(3, 4) == 3:
                    layer -= 1

                if unused[layer]:
                    idx = pick(0, len(unused[layer]) - 1)
                    lit = unused[layer].pop(idx)
                    if mark[abs(lit)]:
                        continue
                else:
                    v = pick(low[layer], high[layer])
                    if mark[v]:
                        continue
                    lit = v * rand_sign()

                lits.append(lit)
                mark[abs(lit)] = True

            # emit clause
            print(" ".join(str(x) for x in lits), "0")
            # clear marks for reuse
            for x in lits:
                mark[abs(x)] = False

    # --- generate equality constraints ---
    for _ in range(eqs):
        while True:
            i = pick(0, nlayers - 1)
            j = pick(0, nlayers - 1)
            a = pick(low[i], high[i])
            b = pick(low[j], high[j])
            if a != b:
                break
        la = a * rand_sign()
        lb = b * rand_sign()
        print(f"{la} {lb} 0")
        print(f"{-la} {-lb} 0")

    # --- generate AND-gate clauses ---
    for gate_arity in arity:
        # pick a head literal
        i = pick(0, nlayers - 1)
        headvar = pick(low[i], high[i])
        mark[headvar] = True
        headlit = headvar * rand_sign()
        print(headlit, end=" ")

        tails = []
        for _ in range(gate_arity):
            j = pick(0, nlayers - 1)
            tvar = pick(low[j], high[j])
            if mark[tvar]:
                continue
            mark[tvar] = True
            tlit = tvar * rand_sign()
            tails.append(tlit)
            print(tlit, end=" ")

        print("0")
        # add binary implications ¬head → ¬tail for each tail
        for tlit in tails:
            print(f"{-headlit} {-tlit} 0")

        # clear marks
        mark[headvar] = False
        for tlit in tails:
            mark[abs(tlit)] = False

if __name__ == "__main__":
    main()
