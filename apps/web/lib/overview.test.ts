import type { ExposureCell } from '@/lib/api';
import { capitalAtRisk, opportunityValue, rollUpPlantExposure } from '@/lib/overview';
import { describe, expect, it } from 'vitest';

function cell(
  location_code: string,
  risk_class: string,
  count: number,
  exposure: number,
): ExposureCell {
  return { location_code, risk_class, count, exposure };
}

describe('rollUpPlantExposure', () => {
  it('sums exposure and count per plant', () => {
    const rows = rollUpPlantExposure([
      cell('PLANT-A', 'critical', 2, 100),
      cell('PLANT-A', 'high', 3, 50),
      cell('PLANT-B', 'moderate', 1, 20),
    ]);
    const a = rows.find((r) => r.plant === 'PLANT-A');
    expect(a).toEqual({ plant: 'PLANT-A', exposure: 150, count: 5 });
  });

  it('ranks plants by exposure, worst first', () => {
    const rows = rollUpPlantExposure([
      cell('PLANT-A', 'low', 1, 10),
      cell('PLANT-B', 'critical', 1, 500),
      cell('PLANT-C', 'high', 1, 80),
    ]);
    expect(rows.map((r) => r.plant)).toEqual(['PLANT-B', 'PLANT-C', 'PLANT-A']);
  });

  it('returns an empty array when there are no cells', () => {
    expect(rollUpPlantExposure([])).toEqual([]);
  });
});

describe('capitalAtRisk', () => {
  it('adds slow/excess and dead-stock value', () => {
    expect(capitalAtRisk(1200, 800)).toBe(2000);
  });
});

describe('opportunityValue', () => {
  it('returns the magnitude of a signed capital delta', () => {
    expect(opportunityValue(-4500)).toBe(4500);
    expect(opportunityValue(4500)).toBe(4500);
  });
});
