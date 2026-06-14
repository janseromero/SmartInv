import { ApprovalStep } from './ApprovalStep.js';

export const States = () => (
  <div className="flex flex-col gap-3">
    <ApprovalStep label="Agent proposed" state="approved" actor="Optimization Agent" />
    <ApprovalStep label="Planner review" state="active" actor="J. Romero" />
    <ApprovalStep label="Manager review" state="pending" />
    <ApprovalStep label="Rejected change" state="rejected" actor="A. Costa" />
  </div>
);
