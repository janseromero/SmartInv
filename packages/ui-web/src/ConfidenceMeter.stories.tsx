import { ConfidenceMeter } from './ConfidenceMeter.js';

export const High = () => <ConfidenceMeter value={0.88} />;

export const Medium = () => <ConfidenceMeter value={0.55} label="Forecast confidence" />;

export const Low = () => <ConfidenceMeter value={0.22} />;

export const WithBands = () => <ConfidenceMeter value={0.66} showBands />;
