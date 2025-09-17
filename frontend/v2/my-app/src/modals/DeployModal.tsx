import { useState } from "react";
import { Dialog, DialogContent, DialogHeader, DialogTitle } from "@/components/ui/dialog";
import { Button } from "@/components/ui/button";
import { Label } from "@/components/ui/label";
import { useDeploy, useStrategies } from "@/api/hooks";

export function DeployModal({
  open,
  onOpenChange,
  defaultTargetDate,
}: {
  open: boolean;
  onOpenChange: (v: boolean) => void;
  defaultTargetDate: string;
}) {
  const { data: strategies } = useStrategies();
  const deploy = useDeploy();

  const [selected, setSelected] = useState<string[]>([]);
  const [date, setDate] = useState(defaultTargetDate);

  const toggle = (id: string) =>
    setSelected((s) => (s.includes(id) ? s.filter((x) => x !== id) : [...s, id]));

  const onSubmit = async () => {
    await deploy.mutateAsync({ target_date: date, strategy_ids: selected });
    onOpenChange(false);
    setSelected([]);
  };

  return (
    <Dialog open={open} onOpenChange={onOpenChange}>
      <DialogContent className="rounded-2xl max-w-lg">
        <DialogHeader>
          <DialogTitle>Deploy Strategies</DialogTitle>
        </DialogHeader>

        <div className="space-y-3">
          <div>
            <Label>Target date</Label>
            <input type="date" className="mt-1 w-full rounded-lg border px-2 py-2"
                   value={date} onChange={(e) => setDate(e.target.value)} />
          </div>

          <div>
            <Label>Select strategies</Label>
            <div className="mt-2 max-h-48 overflow-y-auto rounded border">
              {!strategies?.length ? (
                <div className="p-3 text-sm opacity-70">No strategies.</div>
              ) : (
                strategies.map((s) => (
                  <label key={s.id} className="flex items-center gap-2 p-2 border-b last:border-b-0">
                    <input type="checkbox" checked={selected.includes(s.id)} onChange={() => toggle(s.id)} />
                    <div>
                      <div className="font-medium text-sm">{s.name}</div>
                      <div className="text-xs opacity-70">
                        {s.is_default ? "Default" : "Segmented"} • A/B split {Math.round(s.ab.split * 100)}%
                      </div>
                    </div>
                  </label>
                ))
              )}
            </div>
          </div>

          <div className="pt-2 flex justify-end gap-2">
            <Button variant="outline" onClick={() => onOpenChange(false)}>Cancel</Button>
            <Button onClick={onSubmit} disabled={selected.length === 0 || deploy.isPending}>Deploy</Button>
          </div>
        </div>
      </DialogContent>
    </Dialog>
  );
}