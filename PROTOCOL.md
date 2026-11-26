# Experimental protocol

Estimate the fraction of the first component in a two-component synthetic mixture as spectral separation and measurement noise vary.

- Sample 121 integer coordinates from −60 through 60. Use unit-amplitude Gaussian spectra of width σ = 6 with centers at minus and plus half the separation. Use separations 0.25, 0.5, 1, 2 and 4 times σ.
- Form y = p s₁ + (1 − p) s₂ + ε. Cross each separation with p in {0, 0.1, 0.5, 0.9, 1} and noise SD in {0, 0.01, 0.03, 0.10} relative to peak amplitude. Errors are independent, zero-mean Gaussian. Use NumPy PCG64 seeded with 2026 and visit separation, p, noise SD and replicate in ascending order. Use one observation with no RNG draw at noise SD zero and 100 observations otherwise. The total is 7,525 observations.
- Solve for p on the closed interval [0, 1] using SciPy BVLS (dense exact subsolver, tol 1e−12, 100 iterations maximum) and SLSQP (initial p = 0.5, analytic gradient, ftol 1e−14, 100 iterations maximum). Both minimize squared reconstruction error. The same observations are passed to both solvers.
- Independently compute the optimum as the bounded orthogonal projection onto the line segment joining the two spectra. Identical reference spectra yield a non-identifiable status. Record the Euclidean distance between the spectra for each separation.
- Primary outcome is absolute fraction error in percentage points. Secondary outcome is root mean square reconstruction error per spectral coordinate. Report median and 90th percentile (linear quantile interpolation) by condition and method, including the analytic reference. Summaries exclude failed estimates and report their counts. Preserve solver diagnostics and available candidate estimates in the observation table.
- Validate solver estimates against the analytic optimum within 1e−5 absolute fraction and against the true fraction within 1e−6 in the noiseless cases. Require feasibility within 1e−10 and record every failure against these rules. Run the full experiment twice and compare all table fields with exact categorical agreement and 1e−12 absolute numeric agreement. Report elapsed time as reproduction metadata.
- Plot the preselected 50/50 slice using reference medians for all four noise levels. Use the full grid to assess agreement with the reference. Interpret findings within the synthetic model. The environment is pinned by the accompanying uv lockfile and Python 3.12 series.

## Method references

- [SciPy bounded linear least squares](https://docs.scipy.org/doc/scipy/reference/generated/scipy.optimize.lsq_linear.html)
- [SciPy sequential least squares programming](https://docs.scipy.org/doc/scipy/reference/optimize.minimize-slsqp.html)
