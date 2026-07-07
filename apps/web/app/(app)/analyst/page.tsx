import { AnalystChat } from '@/components/analyst-chat';
import { ROUTE_BY_HREF } from '@/components/nav-config';
import { PageHead } from '@/components/page-head';

const route = ROUTE_BY_HREF.get('/analyst');

export default function Page() {
  if (!route) return null;
  return (
    <div className="h-full flex flex-col px-8 pt-7 pb-6 max-w-[900px] w-full mx-auto">
      <PageHead crumb={route.crumb} title={route.title} sub={route.sub} />
      <div className="flex-1 min-h-0">
        <AnalystChat variant="page" />
      </div>
    </div>
  );
}
