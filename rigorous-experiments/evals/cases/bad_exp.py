"""Demo experiment without discipline."""
import numpy as np

def perm_p(x, y, reps=2000):
    rng = np.random.default_rng(0)
    count = 0
    for _ in range(reps):
        k = int(rng.integers(1, len(y)))
        yr = np.roll(y, k)
        count += abs(np.corrcoef(x, yr)[0, 1]) >= 0.3
    return count / reps
