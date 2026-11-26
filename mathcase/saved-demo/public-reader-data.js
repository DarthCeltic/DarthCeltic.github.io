/* Public-safe reader view derived from the existing saved case records. */
window.MathCaseStaticDemo = {
  "schema": "mathcase-static-demo-r7",
  "mode": "SAVED_EXECUTION_READ_ONLY",
  "source_head": "2f218b8cc94e00c627b43fa0b3a6e0d50e464290",
  "cases": [
    {
      "id": "hero-composite-counterexample-r1",
      "short": "Try it with 4",
      "title": "Does 4 divide the number as well?",
      "kind": "Local arithmetic check",
      "math": "4 ∣ n²  ⇒  4 ∣ n",
      "statement": "For every natural number n, if 4 divides n squared, then 4 divides n.",
      "result": "False at n = 2",
      "status": "COUNTEREXAMPLE_CHECKED",
      "note": "This is a separate local illustrative case. It was checked after the saved prime proof and was not a model error.",
      "steps": [
        {
          "title": "Ask the broad question",
          "body": "For every natural number n, if 4 divides n squared, then 4 divides n."
        },
        {
          "title": "Check n = 2",
          "body": "4 divides 2² = 4, while 4 does not divide 2. The saved exact integer check records the two remainders."
        }
      ]
    },
    {
      "id": "hero-prime-divisibility-r1",
      "short": "Follow the prime proof",
      "title": "What changes when the divisor is prime?",
      "kind": "Saved model attempt + Lean check",
      "math": "p prime ∧ p ∣ n²  ⇒  p ∣ n",
      "statement": "For natural numbers p and n, if p is prime and divides n squared, then p divides n.",
      "result": "Lean check passed",
      "status": "PASSED",
      "note": "The proof is checked for the linked formal statement. No independent review of a plain-language explanation is claimed.",
      "steps": [
        {
          "title": "What are we given?",
          "body": "We know two things about the divisor. It is prime, meaning its only positive factors are 1 and itself and it is greater than 1. It divides the square exactly, leaving no remainder. A proof has to use both facts."
        },
        {
          "title": "Why did the first attempt fail?",
          "body": "Nemotron chose the right rule. To use it, the AI had to show first that the divisor was prime, then that it divided the square. It gave only the second fact. Lean asked for the first one."
        },
        {
          "title": "What did the AI fix?",
          "body": "The question already gave both facts. On its second try, Nemotron supplied them in the order the rule needed. The question stayed the same."
        },
        {
          "title": "Why does the rule work?",
          "body": "A prime dividing a product must divide one of its factors. In a square, both factors are the same number. Lean accepted the corrected proof, and its separate check of the assumptions passed."
        }
      ],
      "proof": "by intro p n hp h; exact Nat.Prime.dvd_of_dvd_pow hp h",
      "proof_sha256": "03602b73efcddecf3f025c5bf6e5b8cfaac5abedc065a9b8c3e0626e4a3e26ca",
      "rejected_attempt": {
        "candidate": "by intro p n hp h; exact Nat.Prime.dvd_of_dvd_pow h",
        "lean_error_excerpt": "/mathcase/input/MathCaseCandidate.lean:4:49: error: Application type mismatch: The argument\n  h\nhas type\n  p ∣ n ^ 2\nbut is expected to have type\n  Nat.Prime ?m.33\nin the application\n  Nat.Prime.dvd_of_dvd_pow h\n'mathcase_candidate' depends on axioms: [propext, sorryAx]\n"
      }
    }
  ],
  "tavily": {
    "case_id": "nat-add-assoc",
    "query": "For all natural numbers n, m, and k, (n + m) + k = n + (m + k). related work prerequisites",
    "result_count": 6,
    "completed_at_utc": "2026-10-26T04:18:36.805941Z",
    "note": "Separate saved nat-add-assoc search. It did not feed the prime-divisibility proof; source snippets are excluded.",
    "path": "saved-demo/tavily-runtime.json"
  }
};
