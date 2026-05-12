# Methodology

This code follows the final report methodology.

## Elderly Demand

For each residential unit `i`:

```text
D_i = population_i * elderly_ratio_i
```

The implementation accepts an existing `elderly_demand` column or computes it from population and elderly-ratio columns.

## Park Quality

For each park `j`, quality is the average of five min-max normalized components:

```text
Q_j = (area_j + transit_j + toilet_j + health_j + elderly_service_j) / 5
```

The components are computed from park area and nearby supporting POIs.

## Distance Decay

The elderly-friendly catchment is `1,500 m`. Within the catchment:

```text
f(d_ij) = exp(-0.5 * (d_ij / 750)^2)
```

Parks outside `1,500 m` contribute zero.

## Baselines

Single-access baseline:

```text
A_i_single = max_j Q_j f(d_ij)
```

Multi-access baseline:

```text
A_i_multi = sum_j Q_j f(d_ij)
```

## Optimization

The optimized multi-access score is:

```text
A_i_opt = A_i_0
        + sum_j (alpha y_j + beta z_j) f(d_ij)
        + sum_k gamma x_k f(d_ik)
```

Decision variables:

- `y_j`: upgrade existing park
- `z_j`: add supporting facilities
- `x_k`: build a new candidate park

Report-aligned parameters:

```text
alpha = 0.10
beta = 0.07
gamma = 0.18
cost_upgrade = 3
cost_support = 2
cost_new_park = 5
budget = 100
```

The code solves a binary budgeted selection problem and reports comparable single-access and multi-access optimization results.
