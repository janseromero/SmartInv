import { AnalystChat } from '@/components/analyst-chat';
import { ROUTE_BY_HREF } from '@/components/nav-config';
import { PageHead } from '@/components/page-head';

const route = ROUTE_BY_HREF.get('/analyst');

export default function Page() {
  if (!route) return null;
  return (
    <div className="px-8 pt-7 pb-6 max-w-[900px]">
      <PageHead crumb={route.crumb} title={route.title} sub={route.sub} />
      <AnalystChat variant="page" />
    </div>
  );
}
