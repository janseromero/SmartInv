import { render } from '@testing-library/react';
import { describe, expect, it } from 'vitest';
import { ApprovalStep } from '../ApprovalStep.js';
import { Badge } from '../Badge.js';
import { ConfidenceMeter } from '../ConfidenceMeter.js';
import { EvidenceStrip } from '../EvidenceStrip.js';
import { KpiCard } from '../KpiCard.js';

describe('Badge', () => {
  it('renders status and ai variants', () => {
    const { asFragment } = render(
      <div>
        <Badge label="Healthy" variant="status" tone="ok" />
        <Badge label="AI" variant="ai" />
      </div>,
    );
    expect(asFragment()).toMatchSnapshot();
  });
});

describe('KpiCard', () => {
  it('renders value, delta and loading states', () => {
    const { asFragment } = render(
      <div>
        <KpiCard label="Excess" value="$812K" delta="6.4%" trend="down" status="warn" />
        <KpiCard label="Loading" value="" loading />
      </div>,
    );
    expect(asFragment()).toMatchSnapshot();
  });
});

describe('ConfidenceMeter', () => {
  it('clamps and renders bands', () => {
    const { asFragment } = render(<ConfidenceMeter value={1.5} showBands />);
    expect(asFragment()).toMatchSnapshot();
  });
});

describe('ApprovalStep', () => {
  it('renders each state', () => {
    const { asFragment } = render(
      <div>
        <ApprovalStep label="Approved" state="approved" actor="Agent" />
        <ApprovalStep label="Rejected" state="rejected" />
      </div>,
    );
    expect(asFragment()).toMatchSnapshot();
  });
});

describe('EvidenceStrip', () => {
  it('renders chips with confidence', () => {
    const { asFragment } = render(
      <EvidenceStrip
        items={[{ metric: 'On hand', value: '1,240', sourceHref: '#' }]}
        confidence={0.82}
        modelVersion="minmax-v3"
      />,
    );
    expect(asFragment()).toMatchSnapshot();
  });
});
