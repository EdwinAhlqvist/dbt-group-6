import numpy as np

# ---------- Quadratic (parabola fit) ----------
def quadratic_refine(m):
    """
    Simple quadratic interpolation around max of 3x3 patch.
    Returns dn = [dy, dx] subpixel offset.
    """
    r, c = np.unravel_index(np.argmax(m), m.shape)
    if 0 < r < m.shape[0]-1 and 0 < c < m.shape[1]-1:
        dx = 0.5 * (m[r, c+1] - m[r, c-1]) / (m[r, c+1] - 2*m[r, c] + m[r, c-1])
        dy = 0.5 * (m[r+1, c] - m[r-1, c]) / (m[r+1, c] - 2*m[r, c] + m[r-1, c])
    else:
        dx, dy = 0.0, 0.0
    return np.array([dy, dx])


# ---------- Chebyshev polynomial approximation ----------
# Mostly translated from MATLAB code by Mikael Sjödahl
def chebyshev_eval(xy, a):
    x, y = xy
    T1x = x; T2x = 2*x**2 - 1; dT2x = 4*x
    T1y = y; T2y = 2*y**2 - 1; dT2y = 4*y

    T = np.array([1, T1y, T2y, T1x, T1x*T1y, T1x*T2y, T2x, T2x*T1y, T2x*T2y])
    dTx = np.array([0,0,0,1, T1y, T2y, dT2x, dT2x*T1y, dT2x*T2y])
    dTy = np.array([0,1,dT2y,0, T1x, T1x*dT2y, 0, T2x, T2x*dT2y])
    d2Txx = np.array([0,0,0,0,0,0,4,4*T1y,4*T2y])
    d2Txy = np.array([0,0,0,0,1,dT2y,0,dT2x,dT2x*dT2y])
    d2Tyy = np.array([0,0,4,0,0,4*T1x,0,0,4*T2x])

    C = T @ a
    dC = np.array([dTx @ a, dTy @ a])
    d2C = np.array([[d2Txx @ a, d2Txy @ a],
                    [d2Txy @ a, d2Tyy @ a]])
    return C, dC, d2C


def subpixel_chebyshev(m):
    """
    Subpixel peak refinement using Chebyshev expansion.
    m : 3x3 patch around peak
    Returns (dn, Cpeak)
    """
    b = m.flatten()
    pts = [-1, 0, 1]
    Tmat = []
    for yy in pts:
        for xx in pts:
            row = [
                1, yy, 2*yy**2-1, xx,
                xx*yy, xx*(2*yy**2-1),
                2*xx**2-1, (2*xx**2-1)*yy, (2*xx**2-1)*(2*yy**2-1)
            ]
            Tmat.append(row)
    Tmat = np.array(Tmat)
    a = np.linalg.solve(Tmat, b)

    xy = np.array([0.0, 0.0])
    for _ in range(5):
        C, dC, d2C = chebyshev_eval(xy, a)
        try:
            step = np.linalg.solve(d2C, -dC)
        except np.linalg.LinAlgError:
            break
        xy += step
        if np.linalg.norm(step) < 1e-6:
            break

    C, _, _ = chebyshev_eval(xy, a)
    return xy, C
