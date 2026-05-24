import numpy as np
from scipy.integrate import solve_ivp
import sympy as sp

def prepare_symbolic(equations, conditions):
    n = len(equations)
    c_eqs = [e.replace('np.', '').replace('x[', 'x').replace(']', '') for e in equations]
    c_conds = [c.replace('np.', '').replace('xa[', 'xa').replace('xb[', 'xb').replace(']', '') for c in conditions]

    t = sp.Symbol('t')
    x_s = sp.symbols(f'x0:{n}')
    xa_s = sp.symbols(f'xa0:{n}')
    xb_s = sp.symbols(f'xb0:{n}')

    d = {'e': sp.E, 'pi': sp.pi}
    
    f_ex = [sp.sympify(e, locals=d) for e in c_eqs]
    R_ex = [sp.sympify(c, locals=d) for c in c_conds]

    f_m = sp.Matrix(f_ex)
    R_m = sp.Matrix(R_ex)

    Jf_m = f_m.jacobian(x_s)
    JRa_m = R_m.jacobian(xa_s)
    JRb_m = R_m.jacobian(xb_s)

    f_l = sp.lambdify((t, x_s), f_ex, 'numpy')
    R_l = sp.lambdify((xa_s, xb_s), R_ex, 'numpy')
    Jf_l = sp.lambdify((t, x_s), Jf_m, 'numpy')
    JRa_l = sp.lambdify((xa_s, xb_s), JRa_m, 'numpy')
    JRb_l = sp.lambdify((xa_s, xb_s), JRb_m, 'numpy')

    def f_ext(t_v, x_v):
        return np.array(f_l(t_v, x_v), dtype=float).flatten()
        
    def R_ext(xa_v, xb_v):
        return np.array(R_l(xa_v, xb_v), dtype=float).flatten()

    def Jf_ext(t_v, x_v):
        res = Jf_l(t_v, x_v)
        if np.isscalar(res) or np.array(res).ndim == 0:
            return np.full((n, n), res, dtype=float)
        return np.array(res, dtype=float).reshape((n, n))

    def JRa_ext(xa_v, xb_v):
        res = JRa_l(xa_v, xb_v)
        if np.isscalar(res) or np.array(res).ndim == 0:
            return np.full((n, n), res, dtype=float)
        return np.array(res, dtype=float).reshape((n, n))

    def JRb_ext(xa_v, xb_v):
        res = JRb_l(xa_v, xb_v)
        if np.isscalar(res) or np.array(res).ndim == 0:
            return np.full((n, n), res, dtype=float)
        return np.array(res, dtype=float).reshape((n, n))

    return f_ext, R_ext, Jf_ext, JRa_ext, JRb_ext

def _solve_inner(f_e, Jf_e, y0, t_s, a, b, rtol=1e-6, atol=1e-8):
    n = len(y0)
    
    def rhs_i(_t, _Y):
        x = _Y[:n]
        Ph = _Y[n:].reshape((n, n))
        j_a = Jf_e(_t, x)
        dPh = j_a @ Ph
        return np.concatenate((f_e(_t, x), dPh.flatten()))

    Y0 = np.concatenate((y0, np.eye(n).flatten()))

    if abs(b - t_s) > 1e-12:
        sol_f = solve_ivp(rhs_i, (t_s, b), Y0, method="DOP853", rtol=rtol, atol=atol)
        if not sol_f.success:
            raise RuntimeError(f"Forward integration failed: {sol_f.message}")
        xb = sol_f.y[:n, -1]
        dY_db = sol_f.y[n:, -1].reshape((n, n))
    else:
        xb = y0.copy()
        dY_db = np.eye(n)

    if abs(a - t_s) > 1e-12:
        sol_b = solve_ivp(rhs_i, (t_s, a), Y0, method="DOP853", rtol=rtol, atol=atol)
        if not sol_b.success:
            raise RuntimeError(f"Backward integration failed: {sol_b.message}")
        xa = sol_b.y[:n, -1]
        dY_da = sol_b.y[n:, -1].reshape((n, n))
    else:
        xa = y0.copy()
        dY_da = np.eye(n)

    return xa, xb, dY_da, dY_db

def _compute_phi(R_e, JRa_e, JRb_e, f_e, Jf_e, p, t_s, a, b):
    try:
        xa, xb, dY_da, dY_db = _solve_inner(f_e, Jf_e, p, t_s, a, b)
        ph_v = R_e(xa, xb)
        ph_j = JRa_e(xa, xb) @ dY_da + JRb_e(xa, xb) @ dY_db
        
        if np.any(np.isnan(ph_v)) or np.any(np.isinf(ph_v)):
            return None
            
        return ph_v, ph_j, xa
    except Exception as e:
        print(f"Error in _compute_phi: {e}")
        return None

def solve_boundary(equations, conditions, p0, t_star, a, b, step_mu, tol, max_iter):
    history = []
    p = np.array(p0, dtype=float)
    
    f_e, R_e, Jf_e, JRa_e, JRb_e = prepare_symbolic(equations, conditions)
    
    res_list = []
    sol_f_last = None
    xa_final = None

    mu_hist = [0.0]
    p_hist = [p.copy()]

    p_str = ", ".join(f"p{i+1}={x:.4f}" for i, x in enumerate(p))
    history.append(f"INIT: {p_str}")
    
    init_res = _compute_phi(R_e, JRa_e, JRb_e, f_e, Jf_e, p, t_star, a, b)
    if init_res is None:
        history.append("ERR: INIT CAUCHY PROBLEM FAILED")
        return {'solution': p, 'converged': False, 'iterations': 0, 'residuals': [float('inf')], 
                'residual': float('inf'), 'sol_forward': None, 'history': history, 
                'message': "Start error.", 'mu_history': mu_hist, 'p_history': p_hist}
    
    ph_fix = init_res[0].copy()

    mu_cur = 0.0
    it = 0
    
    while mu_cur < 1.0 and it < max_iter:
        it += 1
        mu_n = min(mu_cur + step_mu, 1.0)
        
        res = _compute_phi(R_e, JRa_e, JRb_e, f_e, Jf_e, p, t_star, a, b)
        if res is None:
            history.append(f"ERR: CAUCHY PROBLEM FAILED (ITER {it})")
            break
            
        ph_v, ph_j, _ = res
        curr_res = float(np.linalg.norm(ph_v))
        res_list.append(curr_res)
        
        p_str = ", ".join(f"p{i+1}={x:.4f}" for i, x in enumerate(p))
        history.append(f"№{it} (mu={mu_cur:.3f}->{mu_n:.3f}): {p_str}   R={curr_res:.2e}")

        try:
            det_j = np.linalg.det(ph_j)
            if abs(det_j) < 1e-12:
                history.append("ERR: SINGULAR JACOBIAN")
                break
        except:
            history.append("ERR: JACOBIAN COMPUTATION FAILED")
            break

        def rhs_out(_mu, p_c):
            r_in = _compute_phi(R_e, JRa_e, JRb_e, f_e, Jf_e, p_c, t_star, a, b)
            if r_in is None:
                return np.full_like(p_c, np.nan)
            _, ph_j_c, _ = r_in
            try:
                return np.linalg.solve(ph_j_c, -ph_fix)
            except np.linalg.LinAlgError:
                return np.full_like(p_c, np.nan)

        sol_out = solve_ivp(
            rhs_out, t_span=(mu_cur, mu_n), y0=p, method="DOP853", 
            max_step=step_mu, rtol=1e-5, atol=1e-7
        )

        if not sol_out.success:
            history.append(f"ERR: INTEGRATOR FAILED (mu={mu_cur:.3f})")
            break

        p = sol_out.y[:, -1]
        mu_cur = mu_n
        
        mu_hist.append(mu_cur)
        p_hist.append(p.copy())

    history.append("--- КОРРЕКЦИЯ РЕШЕНИЯ (МЕТОД НЬЮТОНА) ---")
    f_res = float('inf')
    
    for n_it in range(15):
        r_f = _compute_phi(R_e, JRa_e, JRb_e, f_e, Jf_e, p, t_star, a, b)
        if r_f is None:
            history.append("ERR: NEWTON POLISHING FAILED")
            break
            
        ph_v, ph_j, xa_final = r_f
        f_res = float(np.linalg.norm(ph_v))
        res_list.append(f_res)
        
        p_str_f = ", ".join(f"p{i+1}={x:.6f}" for i, x in enumerate(p))
        history.append(f"№_N{n_it+1} (mu=1.000): {p_str_f}   R={f_res:.2e}")
        
        if f_res < tol:
            break
            
        try:
            dp = np.linalg.solve(ph_j, -ph_v)
            p = p + dp
            mu_hist.append(1.0)
            p_hist.append(p.copy())
        except np.linalg.LinAlgError:
            history.append("ERR: SINGULAR JACOBIAN IN NEWTON")
            break

    if xa_final is not None and f_res < tol * 100:
        try:
            def rhs_f(_t, _x): return f_e(_t, _x)
            sol_f_last = solve_ivp(rhs_f, (a, b), xa_final, 
                                        method="DOP853", rtol=1e-6, atol=1e-8, 
                                        dense_output=True)
        except Exception as e:
            history.append(f"ERR: FINAL INTEGRATION FAILED: {e}")
            sol_f_last = None

    conv = f_res < tol
    history.append("STATUS: CONVERGED" if conv else "STATUS: NOT CONVERGED")

    return {
        'solution': p,
        'converged': conv,
        'iterations': it,
        'residuals': res_list,
        'residual': f_res,
        'sol_forward': sol_f_last,
        'history': history,
        'message': f"{'OK' if conv else 'FAIL'} iter={it} R={f_res:.2e}",
        'mu_history': mu_hist,
        'p_history': p_hist
    }