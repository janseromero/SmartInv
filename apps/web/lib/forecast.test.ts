import { DEFAULT_CHART_DIMS, forecastChartGeometry } from '@/lib/forecast';
import { describe, expect, it } from 'vitest';

const bands = { p50: 10, p80: 20, p95: 30 };

describe('forecastChartGeometry', () => {
  it('emits one bar per history period', () => {
    const g = forecastChartGeometry([1, 2, 3, 4], bands, 12);
    expect(g.bars).toHaveLength(4);
  });

  it('scales yMax to the largest of history and the top band, with headroom', () => {
    const g = forecastChartGeometry([5, 40], bands, 12);
    expect(g.yMax).toBeCloseTo(40 * 1.1);
  });

  it('orders band Ys so higher value sits higher on screen (smaller y)', () => {
    const g = forecastChartGeometry([1, 2, 3], bands, 12);
    expect(g.p95Y).toBeLessThanOrEqual(g.p80Y);
    expect(g.p80Y).toBeLessThanOrEqual(g.p50Y);
  });

  it('places the "now" divider after the history, inside the plot', () => {
    const g = forecastChartGeometry([1, 2, 3], bands, 12);
    expect(g.nowX).toBeGreaterThan(DEFAULT_CHART_DIMS.padLeft);
    expect(g.nowX).toBeLessThan(DEFAULT_CHART_DIMS.width - DEFAULT_CHART_DIMS.padRight);
    expect(g.forecastX0).toBe(g.nowX);
  });

  it('gives non-negative bar heights that grow with value', () => {
    const g = forecastChartGeometry([2, 8], bands, 6);
    const [low, high] = g.bars;
    expect(low?.height ?? -1).toBeGreaterThanOrEqual(0);
    expect(high?.height ?? 0).toBeGreaterThan(low?.height ?? 0);
  });

  it('never divides by zero on empty history', () => {
    const g = forecastChartGeometry([], bands, 12);
    expect(g.bars).toHaveLength(0);
    expect(Number.isFinite(g.nowX)).toBe(true);
  });
});
