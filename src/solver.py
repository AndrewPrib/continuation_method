import numpy as np
from scipy.integrate import solve_ivp

def _parse_f(equations):
    def f(t, x):
        namespace = {"t": t, "x": x, "np": np}
        return np.array([eval(eq, namespace) for eq in equations], dtype=float)
    return f

def _parse_r(conditions):
    def r(xa, xb):
        namespace = {"xa": xa, "xb": xb, "np": np}
        return np.array([eval(eq, namespace) for eq in conditions], dtype=float)
    return r

def _jacobian_x(f, t, x, eps=1e-7):
    n = len(x)
    fx = f(t, x)
    jac = np.zeros((n, n))
    for j in range(n):
        x_plus = x.copy(); x_plus[j] += eps
        jac[:, j] = (f(t, x_plus) - fx) / eps
    return jac

def _jacobian_r(r, xa, xb, eps=1e-7):
    n = len(xa)
    r_val = r(xa, xb)
    jac_a, jac_b = np.zeros((n, n)), np.zeros((n, n))
    for j in range(n):
        xa_plus = xa.copy(); xa_plus[j] += eps
        jac_a[:, j] = (r(xa_plus, xb) - r_val) / eps
        xb_plus = xb.copy(); xb_plus[j] += eps
        jac_b[:, j] = (r(xa, xb_plus) - r_val) / eps
    return jac_a, jac_b

def _solve_inner(f, p, t_star, a, b, rtol=1e-8, atol=1e-10):
    n = len(p)
    def rhs_inner(_t, y):
        x, x_mat = y[:n], y[n:].reshape(n, n)
        dx = f(_t, x)
        dx_mat = _jacobian_x(f, _t, x) @ x_mat
        return np.concatenate([dx, dx_mat.ravel()])

    y0 = np.concatenate([p, np.eye(n).ravel()])
    sol_f = solve_ivp(rhs_inner, (t_star, b), y0, method="RK45", rtol=rtol, atol=atol, dense_output=True)
    if not sol_f.success: return None
    
    if np.isclose(t_star, a):
        xa, x_mat_a = p.copy(), np.eye(n)
    else:
        sol_b = solve_ivp(rhs_inner, (t_star, a), y0, method="RK45", rtol=rtol, atol=atol, dense_output=True)
        if not sol_b.success: return None
        y_a = sol_b.sol(a)
        xa, x_mat_a = y_a[:n], y_a[n:].reshape(n, n)

    y_b = sol_f.sol(b)
    return xa, y_b[:n], x_mat_a, y_b[n:].reshape(n, n), sol_f

def _compute_phi(r, f, p, t_star, a, b):
    res = _solve_inner(f, p, t_star, a, b)
    if res is None: return None
    xa, xb, x_mat_a, x_mat_b, sol_f = res
    phi_val = r(xa, xb)
    ja, jb = _jacobian_r(r, xa, xb)
    return phi_val, ja @ x_mat_a + jb @ x_mat_b, sol_f

def solve_boundary(equations, conditions, p0, t_star, a, b, step_mu, tol, max_iter):
    p = np.array(p0, dtype=float)
    f, r = _parse_f(equations), _parse_r(conditions)
    residuals, sol_f_last = [], None

    for i in range(1, max_iter + 1):
        res = _compute_phi(r, f, p, t_star, a, b)
        if res is None: return {'message': "Ошибка во внутренней задаче Коши.", 'sol_forward': None}
        phi_val, phi_jac, sol_f_last = res
        err = np.linalg.norm(phi_val)
        residuals.append(err)
        if err < tol: return {'message': f"Сходимость достигнута! Невязка: {err:.2e}", 'sol_forward': sol_f_last}
        
        def rhs_outer(_mu, p_cur):
            inner = _compute_phi(r, f, p_cur, t_star, a, b)
            if inner is None: return np.nan
            return np.linalg.solve(inner[1], -phi_val)

        sol_out = solve_ivp(rhs_outer, (0, 1), p, method="RK45", max_step=step_mu)
        if not sol_out.success: return {'message': "Ошибка внешней задачи (метод продолжения).", 'sol_forward': sol_f_last}
        p = sol_out.y[:, -1]
    return {'message': "Итерации исчерпаны.", 'sol_forward': sol_f_last}