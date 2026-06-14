import { Badge } from './Badge.js';

export const Neutral = () => <Badge label="Excess" />;

export const StatusTones = () => (
  <div className="flex gap-2">
    <Badge label="Healthy" variant="status" tone="ok" />
    <Badge label="Watch" variant="status" tone="warn" />
    <Badge label="Critical" variant="status" tone="crit" />
  </div>
);

export const Ai = () => <Badge label="AI-generated" variant="ai" />;
