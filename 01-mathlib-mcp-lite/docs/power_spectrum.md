# power_spectrum

## Purpose

Report frequency bins in hertz and the one-sided power of a real sequence.

## When to use and when not

Use this when: You have real samples and a sample rate, and you want power per frequency.

Do not use this when: The series is complex, or you need a transform you can invert. Use fft.

## Parameters

| Name | Type | Default | Allowed | Description |
|---|---|---|---|---|
| samples | list | required |  | A 1-D list of real samples. |
| sample_rate_hz | number | required |  | Sample rate in hertz. Must be positive. |

## Returns

frequencies_hz from rfftfreq, power equal to abs(rfft)^2 / n, plus shape and dtype. This is not a power spectral density.

## Conventions

- Input is real. A complex object is rejected.
- At most 4096 elements are accepted. One complex number counts as one element.
- frequencies_hz[0] is 0 Hz. The last bin is the Nyquist frequency when n is even.
- power is abs(rfft(samples))^2 divided by the number of samples.

## Common mistakes

- Treating power as a density in units of power per hertz.
- Ignoring frequencies_hz and assuming a bin index is already in hertz.
- Passing a complex series.

## Minimal example

```json
{
  "sample_rate_hz": 8.0,
  "samples": [
    1.0,
    0.0,
    -1.0,
    0.0
  ]
}
```

```json
{
  "dtype": "float64",
  "frequencies_hz": [
    0.0,
    2.0,
    4.0
  ],
  "power": [
    0.0,
    1.0,
    0.0
  ],
  "shape": [
    3
  ]
}
```

## Related tools

- fft is the transform to use when you will invert it or the input is complex.
