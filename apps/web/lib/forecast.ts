/**
 * Pure geometry for the hand-rolled demand-forecast chart (CV3.E1).
 *
 * No React/SVG here — just the math that turns a bucketed history plus flat
 * Croston/TSB bands into plot coordinates, so it is unit-testable in node.
 * The forecast is a constant per-period rate (p50) with per-period p80/p95
 * bands — faithful to `forecast-croston-v1`, which does not produce a curve.
 */

export interface ForecastBands {
  p50: number;
  p80: number;
  p95: number;
}

export interface ChartDims {
  width: number;
  height: number;
  padTop: number;
  padBottom: number;
  padLeft: number;
  padRight: number;
}

export interface ForecastBar {
  x: number;
  y: number;
  width: number;
  height: number;
  value: number;
}

export interface ForecastGeometry {
  yMax: number;
  bars: ForecastBar[];
  nowX: number;
  forecastX0: number;
  forecastX1: number;
  p50Y: number;
  p80Y: number;
  p95Y: number;
  baselineY: number;
}

export const DEFAULT_CHART_DIMS: ChartDims = {
  width: 640,
  height: 220,
  padTop: 12,
  padBottom: 24,
  padLeft: 8,
  padRight: 8,
};

/** Build plot coordinates for `history` bars + a flat forecast band. */
export function forecastChartGeometry(
  history: number[],
  bands: ForecastBands,
  horizon: number,
  dims: ChartDims = DEFAULT_CHART_DIMS,
): ForecastGeometry {
  const left = dims.padLeft;
  const right = dims.width - dims.padRight;
  const top = dims.padTop;
  const bottom = dims.height - dims.padBottom;
  const plotWidth = Math.max(1, right - left);
  const plotHeight = Math.max(1, bottom - top);

  const yMax = Math.max(1, ...history, bands.p95) * 1.1;
  const yOf = (value: number): number => bottom - (value / yMax) * plotHeight;

  const slots = Math.max(1, history.length + horizon);
  const slotWidth = plotWidth / slots;
  const barWidth = slotWidth * 0.7;

  const bars: ForecastBar[] = history.map((value, i) => {
    const y = yOf(value);
    return {
      x: left + i * slotWidth + (slotWidth - barWidth) / 2,
      y,
      width: barWidth,
      height: Math.max(0, bottom - y),
      value,
    };
  });

  const nowX = left + history.length * slotWidth;

  return {
    yMax,
    bars,
    nowX,
    forecastX0: nowX,
    forecastX1: right,
    p50Y: yOf(bands.p50),
    p80Y: yOf(bands.p80),
    p95Y: yOf(bands.p95),
    baselineY: bottom,
  };
}
