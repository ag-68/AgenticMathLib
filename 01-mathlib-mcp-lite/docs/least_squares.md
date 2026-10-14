# least_squares

## Purpose

Find x that minimizes the 2-norm of A x - b.

## When to use and when not

Use this when: A is rectangular, or a square system may be singular.

Do not use this when: A is square and invertible. Use solve_linear_system for that case.

## Parameters

| Name | Type | Default | Allowed | Description |
|---|---|---|---|---|
| a | list of lists or object | required |  | The matrix A, square or rectangular. A real array is a list of numbers. Complex values are {"re": [...], "im": [...]} with matching shapes. |
| b | list or object | required |  | The right-hand side, one value per row of A. |

## Returns

The solution vector, residual_norm (the 2-norm of A x - b), and rank.

## Conventions

- A real array is a list of numbers.
- Complex values are {"re": [...], "im": [...]} with matching shapes.
- At most 4096 elements are accepted. One complex number counts as one element.
- b has one entry per row of A, not per column.
- rank below the number of columns means the solution is not unique.

## Common mistakes

- Reading residual_norm as zero when the system is only approximately consistent.
- Ignoring rank when several solutions fit equally well.

## Minimal example

```json
{
  "a": [
    [
      1.0,
      0.0
    ],
    [
      0.0,
      1.0
    ],
    [
      1.0,
      1.0
    ]
  ],
  "b": [
    1.0,
    2.0,
    3.0
  ]
}
```

```json
{
  "dtype": "float64",
  "rank": 2,
  "residual_norm": 1.336885555457667e-15,
  "shape": [
    2
  ],
  "values": [
    0.999999999999999,
    2.000000000000001
  ]
}
```

## Related tools

- solve_linear_system is the direct solver for a square invertible matrix.
