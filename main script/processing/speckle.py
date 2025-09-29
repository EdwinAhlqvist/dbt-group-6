# Calculates displacement and correlation images using pixel intensity data of images.
# Correlation calculations are based on the zero mean cross-correlation method (ZMCC).

import numpy as np
from numpy.fft import fft2, ifft2, fftshift
from concurrent.futures import ProcessPoolExecutor, as_completed
from functools import partial
import math

# Internal imports
from processing.subpixel_refinement import quadratic_refine, subpixel_chebyshev

def average_frames(frames, method='mean'):
    """frames: list or array shape (Nframes, H, W)"""
    arr = np.asarray(frames)
    if method == 'mean':
        return np.mean(arr, axis=0)
    elif method == 'median':
        return np.median(arr, axis=0)
    else:
        raise ValueError("method must be 'mean' or 'median'")

def temporal_contrast(frames):
    """Temporal speckle contrast K = std / mean (frames: N,H,W)"""
    arr = np.asarray(frames).astype(np.float32)
    mean = np.mean(arr, axis=0)
    std = np.std(arr, axis=0)
    # Avoid divide by zero
    with np.errstate(divide='ignore', invalid='ignore'):
        K = np.where(mean > 0, std / mean, 0.0)
    return K

# ---- helpers for correlation and peak finding ----
def fftcorr_subwindow(I1_win, I2_win):
    """
    Compute normalized cross-correlation between two windows (M x M).
    Returns correlation matrix c of size (2M x 2M).
    """
    M = I1_win.shape[0]
    big = 2 * M
    # place windows centered in big array
    P = M // 2
    i1 = np.zeros((big, big), dtype=np.float32)
    i2 = np.zeros_like(i1)
    i1[P:P+M, P:P+M] = I1_win - np.mean(I1_win)
    i2[P:P+M, P:P+M] = I2_win - np.mean(I2_win)

    in1 = i1 * i1
    in2 = i2 * i2

    # shift only reference (i1)
    f11 = fft2(fftshift(i1))
    f22 = fft2(i2)
    u12 = f11 * np.conjugate(f22)
    U12 = fft2(u12)
    I12 = np.abs(U12)
    norm = (big ** 2) * math.sqrt(np.sum(in1) * np.sum(in2))
    if norm == 0:
        return np.zeros_like(I12)
    c = I12 / norm
    return c

def integer_peak_from_corr(c):
    """
    Given correlation array c (2M x 2M), return integer displacement D = [dy, dx]
    measured relative to center (center index = M, M).
    """
    big = c.shape[0]
    M = big // 2
    # find global maximum
    idx = np.argmax(c)
    r, col = divmod(idx, big)
    dy = r - M   # positive means shift down (rows)
    dx = col - M # positive means shift right (cols)
    return np.array([dy, dx], dtype=float), (r, col)

def subpixel_from_3x3(c, peak_r, peak_c):
    """
    Fit a 1D quadratic in x and y separately using values at -1,0,+1
    Return fractional correction [dy, dx] (subpixel) relative to integer peak.
    Uses formula: delta = (c[-1] - c[+1]) / (2*(c[-1] - 2*c0 + c[+1])) (if denom!=0)
    """
    big = c.shape[0]
    # ensure we have a 3x3 inside bounds
    if peak_r <= 0 or peak_r >= big-1 or peak_c <= 0 or peak_c >= big-1:
        return np.array([0.0, 0.0])
    # extract 3 points in y for center column
    cy_m = c[peak_r-1, peak_c]
    cy_0 = c[peak_r,   peak_c]
    cy_p = c[peak_r+1, peak_c]
    denom_y = 2.0*(cy_m - 2.0*cy_0 + cy_p)
    if denom_y == 0:
        dy = 0.0
    else:
        dy = (cy_m - cy_p) / denom_y

    # extract 3 points in x for center row
    cx_m = c[peak_r, peak_c-1]
    cx_0 = cy_0
    cx_p = c[peak_r, peak_c+1]
    denom_x = 2.0*(cx_m - 2.0*cx_0 + cx_p)
    if denom_x == 0:
        dx = 0.0
    else:
        dx = (cx_m - cx_p) / denom_x

    # clamp to sensible range (-1..1)
    dy = float(np.clip(dy, -1.0, 1.0))
    dx = float(np.clip(dx, -1.0, 1.0))
    return np.array([dy, dx], dtype=float)


# single-window processing function for parallelization
def process_window(Iref, Iobj, center_r, center_c, M, max_iter=10, tol=1e-3, method='chebyshev'):
    """
    Process one interrogation window centered at (center_r, center_c).
    Returns (u_complex, peak_corr, error_flag)
    u_complex = real = vertical (rows), imag = horizontal (cols)
    """
    H, W = Iref.shape
    half = M//2
    # extract windows with bounds check (pad if necessary)
    r0 = int(center_r - half); c0 = int(center_c - half)
    # pad image if indices go out
    pad_top = max(0, -r0)
    pad_left = max(0, -c0)
    pad_bottom = max(0, r0+M - H)
    pad_right = max(0, c0+M - W)
    if any(p>0 for p in (pad_top, pad_bottom, pad_left, pad_right)):
        # pad both Iref and Iobj with zeros (or reflect) — choose reflect to avoid artificial edges
        ref_p = np.pad(Iref, ((pad_top,pad_bottom),(pad_left,pad_right)), mode='reflect')
        obj_p = np.pad(Iobj, ((pad_top,pad_bottom),(pad_left,pad_right)), mode='reflect')
        r0 += pad_top
        c0 += pad_left
    else:
        ref_p = Iref
        obj_p = Iobj

    I1_win = ref_p[r0:r0+M, c0:c0+M].astype(np.float32)
    I2_win = obj_p[r0:r0+M, c0:c0+M].astype(np.float32)

    # integer loop (at most a few iterations)
    D = np.array([0.0, 0.0])
    e = 0
    snurra = 0
    while True:
        snurra += 1
        c = fftcorr_subwindow(I1_win, I2_win)
        Dcorr, (rpeak, cpeak) = integer_peak_from_corr(c)
        if np.all(Dcorr == 0) or snurra>10 or np.linalg.norm(Dcorr) > M/2:
            D = D + Dcorr
            if snurra>10 or np.linalg.norm(Dcorr) > M/2:
                e = 1
            break
        D = D + Dcorr
        # shift I2_win integer amount for next iteration
        # For efficiency: perform circular shift inside MxM window
        dy, dx = int(Dcorr[0]), int(Dcorr[1])
        I2_win = np.roll(I2_win, -dy, axis=0)  # negative because we measured I2 relative movement
        I2_win = np.roll(I2_win, -dx, axis=1)
        if snurra>10:
            e = 1
            break

    if e:
        return 0+0j, 0.0, 1

    # subpixel refinement: take 3x3 around peak and compute quadratic correction
    # Initial mask around current peak in c
    small = c  # last computed correlation from integer loop
    # take local 3x3 around (rpeak, cpeak)
    # quadratic polynomials
    
    # --- Subpixel refinement ---
    patch = c[rpeak-1:rpeak+2, cpeak-1:cpeak+2]

    # Choose refinement method
    if method == "quadratic":
        dn = quadratic_refine(patch)
    elif method == "chebyshev":
        dn, Cpeak = subpixel_chebyshev(patch)
    else:
        dn = subpixel_from_3x3(small, rpeak, cpeak)

    

    F = dn.copy()
    snurra = 0
    # iterative fractional refine
    while np.hypot(F[0], F[1]) > tol and snurra < max_iter:
        snurra += 1
        # shift I2_win by fractional F using simple bilinear interpolation
        # create an interpolated window: use scipy? to avoid dependency, implement manual interp
        # but here we'll use numpy's map_coordinates if available; to keep minimal, do simple Fourier shift:
        # apply subpixel shift using phase ramp in Fourier domain
        # shift via multiplication in freq domain (efficient)
        Mbig = M
        # compute Fourier shift
        Freq = fft2(I2_win)
        ky = np.fft.fftfreq(Mbig)
        kx = np.fft.fftfreq(Mbig)
        KX, KY = np.meshgrid(kx, ky)
        phase = np.exp(-2j*np.pi*(F[0]*KY + F[1]*KX))
        I2_shift = np.real(ifft2(Freq * phase))
        c = fftcorr_subwindow(I1_win, I2_shift)
        Dcorr_sub, (rpeak, cpeak) = integer_peak_from_corr(c)
        dn = subpixel_from_3x3(c, rpeak, cpeak)
        F = F + dn
        I2_win = I2_shift  # update for next iter
    if snurra>=max_iter:
        e = 1

    U = D + F
    # final peak correlation value at center region
    peak_corr = c[rpeak, cpeak] if c is not None else 0.0
    u_complex = float(U[0]) + 1j*float(U[1])
    return u_complex, float(peak_corr), int(e)

class SpeckleProcessor:
    def __init__(self, M=64, rows=None, cols=None, n_workers=4):
        """
        M: subwindow size
        rows/cols: center positions (if None auto grid will be used)
        n_workers: parallel workers for windows
        """
        self.M = M
        self.rows = rows
        self.cols = cols
        self.n_workers = n_workers

    def process(self, Iref_stack, Iobj_stack, method='mean'):
        """
        Main entry point.
        Iref_stack: list or array (Nref,H,W)
        Iobj_stack: list or array (Nobj,H,W)
        Returns: u_image (nrows x ncols) as complex, c_image (same), e_image (same), sc_image (temporal contrast)
        """
        # combine stacks
        Iref = average_frames(Iref_stack, method=method)
        Iobj = average_frames(Iobj_stack, method=method)

        # temporal contrast for object stack as QC
        sc_image = temporal_contrast(Iobj_stack)

        H, W = Iref.shape
        # determine grid
        if self.rows is None or self.cols is None:
            step = self.M
            rows = list(range(self.M//2, H - self.M//2, step))
            cols = list(range(self.M//2, W - self.M//2, step))
        else:
            rows = self.rows
            cols = self.cols

        nrows = len(rows)
        ncols = len(cols)

        # prepare outputs
        u_image = np.zeros((nrows, ncols), dtype=np.complex64)
        c_image = np.zeros((nrows, ncols), dtype=np.float32)
        e_image = np.zeros((nrows, ncols), dtype=np.int8)

        # Build list of tasks (row, col)
        # Build list of tasks (row, col)
        tasks = []
        for i, rr in enumerate(rows):
            for j, cc in enumerate(cols):
                tasks.append((i, j, rr, cc))

        # Use ProcessPoolExecutor
        with ProcessPoolExecutor(max_workers=self.n_workers) as ex:
            futures = {ex.submit(process_window, Iref, Iobj, rr, cc, self.M): (i, j)
                    for (i, j, rr, cc) in tasks}
            for future in as_completed(futures):
                i, j = futures[future]
                try:
                    u_complex, peak_corr, err = future.result()
                except Exception:
                    u_complex, peak_corr, err = 0+0j, 0.0, 1
                u_image[i, j] = u_complex
                c_image[i, j] = peak_corr
                e_image[i, j] = err


        return u_image, c_image, e_image, sc_image, rows, cols

