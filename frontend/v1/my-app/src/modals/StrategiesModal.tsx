import { useStrategies } from "@/api/hooks";
import { Dialog, DialogContent, DialogHeader, DialogTitle } from "@/components/ui/dialog";
import { Badge } from "@/components/ui/badge";

export function StrategiesModal({
  open,
  onOpenChange,
  onCreate,
  onDeploy,
}: {
  open: boolean;
  onOpenChange: (v: boolean) => void;
  onCreate: () => void;
  onDeploy: () => void;
}) {
  const { data, isLoading, isError } = useStrategies();

  return (
    <Dialog open={open} onOpenChange={onOpenChange}>
      <DialogContent className="rounded-2xl max-w-2xl">
        <DialogHeader>
          <DialogTitle>All Strategies</DialogTitle>
        </DialogHeader>
        {isLoading ? (
          <p>Loading…</p>
        ) : isError ? (
          <p className="text-red-600 dark:text-red-400">Failed to load strategies.</p>
        ) : (
          <div className="space-y-3">
            <div className="flex gap-2">
              <button className="rounded-lg border px-3 py-1 text-sm" onClick={onCreate}>New Strategy</button>
              <button className="rounded-lg border px-3 py-1 text-sm" onClick={onDeploy}>Deploy to Day…</button>
            </div>
            <ul className="space-y-2">
              {data?.map((s) => (
                <li key={s.id} className="rounded-lg border p-2">
                  <div className="flex items-center justify-between">
                    <div className="font-medium">{s.name}</div>
                    {s.is_default && <Badge variant="secondary">Default</Badge>}
                  </div>
                  <div className="text-xs opacity-70 mt-1">
                    A: {s.ab.A.type} offsets [{s.ab.A.days_of_action.join(", ")}] • B: {s.ab.B.type} offsets [{s.ab.B.days_of_action.join(", ")}]
                  </div>
                </li>
              ))}
            </ul>
          </div>
        )}
      </DialogContent>
    </Dialog>
  );
}