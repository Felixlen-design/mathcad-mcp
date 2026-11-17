"""Kirchhoff annular plate with rigid hub: tilting moment (n=1) and axial force (n=0).
Energy method avoids sign-convention pitfalls: load = 2U/displacement (Clapeyron)."""
import sympy as sp
import numpy as np

r = sp.symbols('r', positive=True)
nu = sp.Rational(33, 100)

def solve_n1(a, b, outer):
    C = sp.symbols('C1:5'); psi = 1
    W = C[0]*r + C[1]*r**3 + C[2]/r + C[3]*r*sp.log(r)
    W1, W2 = sp.diff(W, r), sp.diff(W, r, 2)
    eqs = [W.subs(r, b) - psi*b, W1.subs(r, b) - psi, W.subs(r, a)]
    eqs.append(W1.subs(r, a) if outer == 'clamped' else (W2 + nu*(W1/r - W/r**2)).subs(r, a))
    sol = sp.solve(eqs, C)
    W = W.subs(sol); W1, W2 = sp.diff(W, r), sp.diff(W, r, 2)
    k = W1/r - W/r**2
    integrand = ((W2 + k)**2 - 2*(1-nu)*(W2*k - k**2))*r
    U = sp.pi/2*sp.Integral(integrand, (r, b, a)).evalf(30)   # per D
    M = 2*U/psi                                              # per D
    Mr = sp.lambdify(r, -(W2 + nu*k)); Mt = sp.lambdify(r, -(k + nu*W2))
    rs = np.linspace(float(b), float(a), 2001)
    mmax = max(np.max(np.abs(Mr(rs))), np.max(np.abs(Mt(rs))))
    return float(M), float(mmax)      # M/D/psi, |m|max/D/psi

def solve_n0(a, b, outer):
    C = sp.symbols('C1:5'); d = 1
    W = C[0] + C[1]*r**2 + C[2]*sp.log(r) + C[3]*r**2*sp.log(r)
    W1, W2 = sp.diff(W, r), sp.diff(W, r, 2)
    eqs = [W.subs(r, b) - d, W1.subs(r, b), W.subs(r, a)]
    eqs.append(W1.subs(r, a) if outer == 'clamped' else (W2 + nu*W1/r).subs(r, a))
    sol = sp.solve(eqs, C)
    W = W.subs(sol); W1, W2 = sp.diff(W, r), sp.diff(W, r, 2)
    integrand = ((W2 + W1/r)**2 - 2*(1-nu)*W2*W1/r)*r
    U = sp.pi*sp.Integral(integrand, (r, b, a)).evalf(30)
    F = 2*U/d
    Mr = sp.lambdify(r, -(W2 + nu*W1/r)); Mt = sp.lambdify(r, -(W1/r + nu*W2))
    rs = np.linspace(float(b), float(a), 2001)
    mmax = max(np.max(np.abs(Mr(rs))), np.max(np.abs(Mt(rs))))
    return float(F), float(mmax)

a, b = sp.Rational(553, 10), sp.Rational(365, 10)
E = 70000.0
print('b/a =', float(b/a))
MK = 173.5e3   # N mm
for outer in ('clamped', 'simply'):
    M, m = solve_n1(a, b, outer)
    beta = 6*m*float(a)/M
    print(f'n=1 {outer:8s} beta = {beta:.4f}')
    for t in (10, 12, 14):
        D = E*t**3/(12*(1-0.33**2))
        psi = MK/(M*D)
        print(f'   t={t}: sigma = {beta*MK/(float(a)*t*t):6.2f} N/mm2   tilt = {np.degrees(psi):.5f} deg')
    F, m0 = solve_n0(a, b, outer)
    bF = 6*m0/F
    print(f'n=0 {outer:8s} beta_F = {bF:.4f}  sigma(F=1100,t=12) = {bF*1100/144:.2f} N/mm2')
