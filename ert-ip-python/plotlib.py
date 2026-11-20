import sys, pickle, os
import numpy as np
import matplotlib; matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib.colors import ListedColormap, BoundaryNorm
from matplotlib.ticker import FuncFormatter
from invert import *
from skimage import measure

from config import W, ENTRADA, OUT, HDIR, OUTF, PF, load_topo

# ---- common scales -----------------------------------------------------------------------------
RHO_LEVELS = [5, 10, 20, 40, 70, 100, 150, 250, 400, 700, 1200, 2000, 4000]
RHO_COLORS = ['#00008b', '#0033cc', '#0077ff', '#00bfff', '#00e5e5', '#3ddc84', '#a6e22e', '#f5e61e', '#ffb000', '#ff6a00', '#d7191c', '#8b0a50']
RHO_CMAP = ListedColormap(RHO_COLORS); RHO_NORM = BoundaryNorm(np.log10(RHO_LEVELS), len(RHO_COLORS))
IP_LEVELS = [0, 0.5, 1, 1.5, 2, 2.5, 3, 3.5, 4, 5, 6]
IP_COLORS = ['#08306b', '#2171b5', '#4eb3d3', '#7fcdbb', '#b8e186', '#e6f598', '#fee08b', '#fdae61', '#f46d43', '#a50026']
IP_CMAP = ListedColormap(IP_COLORS); IP_NORM = BoundaryNorm(IP_LEVELS, len(IP_COLORS))

def load_all():
    F = pickle.load(open(W+'final.pkl', 'rb')); R = pickle.load(open(W+'dc_results2.pkl', 'rb'))
    return F, R

def fine_section(g, vals, env_xs, env_D, dxf=0.5, ddf=0.25, log=True):
    """interpolate parameter values onto a fine (x, depth-below-surface) grid, mask by data envelope; returns X, Zelev, V (masked)"""
    vals = np.log10(np.maximum(vals, 1e-3)) if log else vals
    V = vals.reshape(g.nel, g.nz)
    dpar = par_depth(g).reshape(g.nel, g.nz)
    xf = np.arange(0, g.xel[-1]+1e-9, dxf); df_ = np.arange(0, 45.0, ddf)
    col_vals = np.zeros((g.nel, len(df_)))
    for p in range(g.nel):
        col_vals[p] = np.interp(df_, dpar[p], V[p])
    Vf = np.zeros((len(xf), len(df_)))
    for j in range(len(df_)):
        Vf[:, j] = np.interp(xf, g.xel, col_vals[:, j])
    zs = np.interp(xf, g.xel, g.Z[g.ixc0+1+2*np.arange(g.nel), 0])
    Dm = np.interp(xf, env_xs, env_D)
    mask = df_[None, :] > Dm[:, None]
    X = np.repeat(xf[:, None], len(df_), 1); Z = zs[:, None] - df_[None, :]
    return X, Z, np.ma.array(Vf, mask=mask), zs, Dm

def draw_section(ax, g, vals, env, kind='rho', show_contours=True, show_cbar=False, title=None, ylim=None, zones=True, label_xy=None):
    X, Z, V, zs, Dm = fine_section(g, vals, *env, log=(kind == 'rho'))
    if kind == 'rho':
        cs = ax.contourf(X, Z, V, levels=np.log10(RHO_LEVELS), colors=RHO_COLORS, extend='both')
    else:
        cs = ax.contourf(X, Z, V, levels=IP_LEVELS, colors=IP_COLORS, extend='both')
    return X, Z, V, zs, Dm, cs

def rho_fine(g, rho, env):
    return fine_section(g, rho, *env, log=True)

def class_regions(V):
    """label for each fine-grid cell: 0 soft(<100), 1 consolidated (100-400), 2 bedrock (>=400), -1 masked"""
    lab = np.full(V.shape, -1)
    v = np.asarray(V.filled(np.nan))
    lab[(v < 2.0)] = 0; lab[(v >= 2.0) & (v < np.log10(400))] = 1; lab[v >= np.log10(400)] = 2
    lab[np.isnan(v)] = -1
    return lab

def rho_legend(fig, cax=None, orientation='horizontal', label='Resistividad (Ω·m)'):
    sm = plt.cm.ScalarMappable(norm=RHO_NORM, cmap=RHO_CMAP)
    cb = fig.colorbar(sm, cax=cax, orientation=orientation, ticks=np.log10(RHO_LEVELS), fraction=0.05, pad=0.18, aspect=50)
    cb.ax.set_xticklabels([str(l) for l in RHO_LEVELS], fontsize=float(os.environ.get('LEG_FS', 8))); cb.set_label(label, fontsize=float(os.environ.get('LEG_LBL', 9)))
    return cb

def ip_legend(fig, cax=None, orientation='horizontal', label='Cargabilidad (ms)'):
    sm = plt.cm.ScalarMappable(norm=IP_NORM, cmap=IP_CMAP)
    cb = fig.colorbar(sm, cax=cax, orientation=orientation, ticks=IP_LEVELS, fraction=0.05, pad=0.18, aspect=50)
    cb.ax.set_xticklabels([str(l) for l in IP_LEVELS], fontsize=float(os.environ.get('LEG_FS', 8))); cb.set_label(label, fontsize=float(os.environ.get('LEG_LBL', 9)))
    return cb
