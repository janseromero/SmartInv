import { EvidenceStrip } from './EvidenceStrip.js';

const items = [
  { metric: 'On hand', value: '1,240' },
  { metric: 'Avg monthly use', value: '85' },
  { metric: 'Lead time', value: '21d', sourceHref: '#' },
];

export const Default = () => <EvidenceStrip items={items} />;

export const WithConfidence = () => (
  <EvidenceStrip items={items} confidence={0.82} modelVersion="minmax-v3" />
);

export const Loading = () => <EvidenceStrip items={[]} loading />;
