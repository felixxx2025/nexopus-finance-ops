import { Skeleton } from "@/components/ui/skeleton";
import { Card, CardContent, CardHeader } from "@/components/ui/card";

export function DashboardSkeleton() {
  return (
    <div className="space-y-6">
      <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
        {[...Array(4)].map((_, i) => (
          <Card key={i} className="bg-gray-900 border-gray-800">
            <CardHeader className="pb-2">
              <Skeleton className="h-4 w-24 bg-gray-800" />
            </CardHeader>
            <CardContent>
              <Skeleton className="h-8 w-32 bg-gray-800" />
              <Skeleton className="h-3 w-20 bg-gray-800 mt-2" />
            </CardContent>
          </Card>
        ))}
      </div>
      <Card className="bg-gray-900 border-gray-800">
        <CardHeader>
          <Skeleton className="h-6 w-48 bg-gray-800" />
        </CardHeader>
        <CardContent>
          <Skeleton className="h-64 w-full bg-gray-800" />
        </CardContent>
      </Card>
    </div>
  );
}

export function TableSkeleton() {
  return (
    <div className="space-y-3">
      {[...Array(5)].map((_, i) => (
        <div key={i} className="flex items-center gap-4 p-4 bg-gray-900 border border-gray-800 rounded-lg">
          <Skeleton className="h-4 w-32 bg-gray-800" />
          <Skeleton className="h-4 w-24 bg-gray-800" />
          <Skeleton className="h-4 w-20 bg-gray-800" />
          <Skeleton className="h-4 w-40 bg-gray-800 ml-auto" />
        </div>
      ))}
    </div>
  );
}
