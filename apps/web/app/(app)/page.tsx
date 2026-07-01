import { ExecutiveOverview } from '@/components/executive-overview';
import { ROUTE_BY_HREF } from '@/components/nav-config';
import { PageHead } from '@/components/page-head';

const route = ROUTE_BY_HREF.get('/');

export default function Page() {
  if (!route) return null;
  return (
    <div className="px-8 pt-7 pb-15 max-w-[1400px]">
      <PageHead crumb={route.crumb} title={route.title} sub={route.sub} />
      <ExecutiveOverview />
    </div>
  );
}
