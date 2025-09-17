import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";

export function StrategiesCard({ strategies }: { strategies: { id: string; name: string }[] }) {
  return (
    <Card className="rounded-2xl h-full">
      <CardHeader>
        <CardTitle>Strategies</CardTitle>
      </CardHeader>
      <CardContent>
        {strategies.length === 0 ? (
          <p className="text-sm text-neutral-500 dark:text-neutral-400">No strategies deployed to this day.</p>
        ) : (
          <div className="flex flex-wrap gap-2">
            {strategies.map((s) => (
              <Badge key={s.id} variant="secondary" className="rounded-full">{s.name}</Badge>
            ))}
          </div>
        )}
      </CardContent>
    </Card>
  );
}