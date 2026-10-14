# convolve

## Purpose

Compute the linear convolution of two 1-D sequences.

## When to use and when not

Use this when: You want linear convolution in full, same, or valid mode.

Do not use this when: You want circular convolution. This tool does not wrap the edges.

## Parameters

| Name | Type | Default | Allowed | Description |
|---|---|---|---|---|
| a | list or object | required |  | The first 1-D sequence. A real array is a list of numbers. Complex values are {"re": [...], "im": [...]} with matching shapes. |
| b | list or object | required |  | The second 1-D sequence. A real array is a list of numbers. Complex values are {"re": [...], "im": [...]} with matching shapes. |
| mode | string | "full" | full, same, valid | Which part of the full convolution to keep. |

## Returns

The convolved sequence, with shape, dtype, and either values or re and im. same has the length of a. valid keeps only complete overlaps.

## Conventions

- A real array is a list of numbers.
- Complex values are {"re": [...], "im": [...]} with matching shapes.
- At most 4096 elements are accepted. One complex number counts as one element.
- full returns every overlap, including partial ones at the ends.
- same returns the central part and has the same length as a.
- valid returns only positions where b lies entirely inside a.

## Common mistakes

- Using valid when the requested length is the length of a. That is same.
- Expecting the edges to wrap. This is linear convolution.

## Minimal example

```json
{
  "a": [
    1.0,
    2.0,
    3.0
  ],
  "b": [
    1.0,
    1.0
  ],
  "mode": "full"
}
```

```json
{
  "dtype": "float64",
  "shape": [
    4
  ],
  "values": [
    1.0,
    3.0,
    5.0,
    3.0
  ]
}
```

## Related tools

- fft does not replace this tool. This tool is linear convolution.
