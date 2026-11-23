# MathCase guided cases — teacher guide

This is the downloadable copy of the readable [teacher answer page](teacher-guide.html). The examples formalize standard facts; they are not novelty claims.

## Start with the hand calculation

Two squared is four. Four goes into four exactly once. Four does not go into two a whole number of times, so at n = 2 the rule fails. This disproves the unrestricted claim that a divisor of a square must divide its root. It does not show that every composite divisor fails.

## Transfer challenge

Plain statement: if a prime `p` divides `(a*b)^2`, then `p` divides `a` or `p` divides `b`.

Exact Lean proposition supplied to the checker:

```lean
∀ (p a b : Nat), p.Prime → p ∣ (a * b) ^ 2 → p ∣ a ∨ p ∣ b
```

The proof source can use this proposition in a named theorem declaration:

```lean
theorem prime_dvd_factor_of_product_square (p a b : Nat)
    (hp : p.Prime) (h : p ∣ (a * b) ^ 2) : p ∣ a ∨ p ∣ b
```

One proof:

```lean
by
  have hProduct : p ∣ a * b := hp.dvd_of_dvd_pow h
  exact hp.dvd_mul.mp hProduct
```

The first line uses primality to move from a divisor of a square to a divisor of its base. The second applies the prime-divides-product property.

Keep the square and product statements separate. For one square, if `6 ∣ n²`, then `2 ∣ n` and `3 ∣ n`; since 2 and 3 are coprime, `6 ∣ n`. But for the product statement, `a = 2` and `b = 3` give `6 ∣ a*b` while `6 ∤ a` and `6 ∤ b`. So the square-free composite example does not make 6 behave like a prime in the product step.

## Teaching notes

- Ask the learner to compare the exact Lean declaration to the words before checking a proof.
- A Lean check establishes the formal proposition under the imported Lean/Mathlib environment. It does not establish that the informal sentence was translated correctly unless a person checks that separately.
- Keep the learner's failed proofs. A rejected candidate is useful process evidence and should not be silently replaced in a report.
