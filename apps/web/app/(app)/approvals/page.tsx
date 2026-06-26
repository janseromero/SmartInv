import { ApprovalQueue } from '@/components/approval-queue';
import { ROUTE_BY_HREF } from '@/components/nav-config';
import { PageHead } from '@/components/page-head';

const route = ROUTE_BY_HREF.get('/approvals');

export default function Page() {
  if (!route) return null;
  return (
    <div className="px-8 pt-7 pb-15 max-w-[1400px]">
      <PageHead crumb={route.crumb} title={route.title} sub={route.sub} />
      <ApprovalQueue />
    </div>
  );
}
