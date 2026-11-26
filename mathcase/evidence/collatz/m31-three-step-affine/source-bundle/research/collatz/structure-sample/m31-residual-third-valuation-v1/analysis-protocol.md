# M31 residual third-valuation aggregate decomposition v1

This is a derived analysis of the completed third-valuation census, not another
trajectory scan. It may read only the hash-bound `summary.json`, primary
`run-manifest.json`, and independently passing `verification-receipt.json`.

The analysis checks the stored marginal histograms and the independently
verified zero count for fixed-representative third-step descent. The registered
threshold says descent occurs when `a3 >= 3` for `a2 = 1`, and when `a3 >= 2`
for `a2 = 2`. Therefore, zero descent implies all `a2 = 2` cases have `a3 = 1`.
Since the total `a3 = 2` count equals the total `a2 = 2` count, every `a3 = 2`
case belongs to `a2 = 1`. The remaining `a2 = 1` cases have `a3 = 1`.

The output records this exact 2-by-2 count decomposition, confirms that every
observed third valuation is below its registered class-uniformity cutoff, and
states the finite-scope limit. It does not claim a global trajectory rule,
convergence, or a new descent family. It authorizes no further scan.

The analysis receipt binds this protocol, the analysis code, and all three
source artifacts by SHA-256. The derived JSON and receipt are written once to
the existing run directory and are not folded back into the immutable primary
run manifest.
