# solve_linear_system

## Purpose

Solve A x = b when A is square.

## When to use and when not

Use this when: A is square and you want the direct solution plus a residual.

Do not use this when: A is rectangular or singular. Use least_squares.

## Parameters

| Name | Type | Default | Allowed | Description |
|---|---|---|---|---|
| a | list of lists or object | required |  | The matrix A. It must be square. A real array is a list of numbers. Complex values are {"re": [...], "im": [...]} with matching shapes. |
| b | list or object | required |  | The right-hand side, one value per row of A. |

## Returns

The solution vector, with shape, dtype, and residual_norm, the 2-norm of A x - b.

## Conventions

- A real array is a list of numbers.
- Complex values are {"re": [...], "im": [...]} with matching shapes.
- At most 4096 elements are accepted. One complex number counts as one element.
- A must have the same number of rows and columns.
- b has one entry per row.
- residual_norm near zero means the solution fits A x = b.

## Common mistakes

- Passing a rectangular matrix. The error tells you to use least_squares.
- Ignoring a singular error and treating a failure as a numeric answer.

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
    ]
  ],
  "b": [
    3.0,
    4.0
  ]
}
```

```json
{
  "dtype": "float64",
  "residual_norm": 0.0,
  "shape": [
    2
  ],
  "values": [
    3.0,
    4.0
  ]
}
```

## Related tools

- least_squares minimizes ||A x - b|| when A is not square or not invertible.
