"""Inventory-optimization package (CV3.E2).

Operations research, not LLMs. The MVP uses closed-form inventory theory
(safety stock, reorder point, EOQ) plus a seeded Monte-Carlo stockout estimator
and an analytical cost/risk Pareto frontier \u2014 all deterministic and explainable.
Pyomo / OR-Tools and the cross-site transfer LP are deferred (ADR-028). Mirrors
the scoring/forecast packages: ``model`` / ``engine`` / ``service``.
"""
