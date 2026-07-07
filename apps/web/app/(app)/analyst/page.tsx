import { AnalystWorkspace } from '@/components/analyst-workspace';
import { ROUTE_BY_HREF } from '@/components/nav-config';
import { PageHead } from '@/components/page-head';

const route = ROUTE_BY_HREF.get('/analyst');

export default function Page() {
  if (!route) return null;
  return (
    <div className="h-full flex flex-col px-8 pt-7 pb-6 max-w-[1100px] w-full mx-auto">
      <PageHead crumb={route.crumb} title={route.title} sub={route.sub} />
      <AnalystWorkspace />
    </div>
  );
}
