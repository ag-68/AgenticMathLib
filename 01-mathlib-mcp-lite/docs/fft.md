# fft

## Purpose

Transform a 1-D sequence into frequency bins, or restore the sequence.

## When to use and when not

Use this when: You need the forward or inverse discrete Fourier transform of one sequence.

Do not use this when: You want the one-sided power of a real recording. Use power_spectrum.

## Parameters

| Name | Type | Default | Allowed | Description |
|---|---|---|---|---|
| x | list or object | required |  | The 1-D sequence. A real array is a list of numbers. Complex values are {"re": [...], "im": [...]} with matching shapes. |
| direction | string | "forward" | forward, inverse | Which transform to apply. |
| norm | string | "backward" | backward, forward, ortho | Scaling. backward is NumPy's usual unnormalized forward transform. |

## Returns

A complex sequence of the same length, with shape, dtype, re, and im. The inverse of a forward transform uses the same norm and restores the input.

## Conventions

- A real array is a list of numbers.
- Complex values are {"re": [...], "im": [...]} with matching shapes.
- At most 4096 elements are accepted. One complex number counts as one element.
- The default norm is backward, not ortho. An inverse call must use the same norm.
- Bins follow SciPy's fft order: the zero frequency is first.

## Common mistakes

- Assuming the default scaling is orthonormal.
- Inverting with a different norm than the forward call.
- Asking fft for a one-sided power spectrum.

## Minimal example

```json
{
  "direction": "forward",
  "norm": "backward",
  "x": [
    1.0,
    0.0,
    0.0,
    0.0
  ]
}
```

```json
{
  "dtype": "complex128",
  "im": [
    -0.0,
    0.0,
    -0.0,
    -0.0
  ],
  "re": [
    1.0,
    1.0,
    1.0,
    1.0
  ],
  "shape": [
    4
  ]
}
```

## Related tools

- power_spectrum returns frequencies in hertz and one-sided power for a real signal.
- convolve is linear convolution, not multiplication of Fourier transforms.
