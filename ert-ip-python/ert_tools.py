import numpy as np, pandas as pd
from parse_dat import read_dat, FILES
from config import load_topo

TOPO = load_topo()

def load_line(i):
    h, a = read_dat(FILES[i])
    df = pd.DataFrame(a, columns=['x', 'a', 'n', 'rhoa', 'ip'])
    df['A'] = (df.x / 5).round().astype(int)
    df['M'] = ((df.x + df.n * df.a) / 5).round().astype(int)
    df['N'] = ((df.x + df.n * df.a + df.a) / 5).round().astype(int)
    df['B'] = ((df.x + 2 * df.n * df.a + df.a) / 5).round().astype(int)
    df['xmid'] = df.x + df.n * df.a + df.a / 2
    df['k'] = np.pi * df.n * (df.n + 1) * df.a           # flat-earth geometric factor
    # pseudo-depth (median depth of investigation approx. Edwards / Barker), Wenner-Schlumberger ~ 0.17 L (L = array length)
    df['L'] = 2 * df.n * df.a + df.a
    return h, df

def rms_rel(obs, calc):
    return 100 * np.sqrt(np.mean(((obs - calc) / obs) ** 2))

def rms_log(obs, calc):
    return 100 * np.sqrt(np.mean((np.log(obs) - np.log(calc)) ** 2))
