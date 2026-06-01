import dynamic from 'next/dynamic';

// Lazy load heavy chart components
export const Chart = dynamic(() => import('recharts').then(mod => mod.ResponsiveContainer), {
  loading: () => <div className="h-64 animate-pulse bg-muted rounded" />,
  ssr: false,
});

export const LineChart = dynamic(() => import('recharts').then(mod => mod.LineChart), {
  loading: () => <div className="h-64 animate-pulse bg-muted rounded" />,
  ssr: false,
});

export const BarChart = dynamic(() => import('recharts').then(mod => mod.BarChart), {
  loading: () => <div className="h-64 animate-pulse bg-muted rounded" />,
  ssr: false,
});
