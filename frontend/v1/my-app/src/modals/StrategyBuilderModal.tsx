import { useState } from "react";
import { Dialog, DialogContent, DialogHeader, DialogTitle } from "@/components/ui/dialog";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select";
import { useCreateStrategy } from "@/api/hooks";

type Props = { open: boolean; onOpenChange: (v: boolean) => void };

const AGE_BUCKETS = [
  { key: "all", label: "All ages", range: null as null | { min: number; max: number } },
  { key: "18_24", label: "18–24", range: { min: 18, max: 24 } },
  { key: "25_34", label: "25–34", range: { min: 25, max: 34 } },
  { key: "35_44", label: "35–44", range: { min: 35, max: 44 } },
  { key: "45_54", label: "45–54", range: { min: 45, max: 54 } },
  { key: "55_64", label: "55–64", range: { min: 55, max: 64 } },
  { key: "65_85", label: "65–85", range: { min: 65, max: 85 } },
];

const RISK_BUCKETS = [
  { key: "all", label: "All risks", range: null as null | { min: number; max: number } },
  { key: "0_0.2", label: "0.0 – 0.2", range: { min: 0.0, max: 0.2 } },
  { key: "0.2_0.4", label: "0.2 – 0.4", range: { min: 0.2, max: 0.4 } },
  { key: "0.4_0.6", label: "0.4 – 0.6", range: { min: 0.4, max: 0.6 } },
  { key: "0.6_0.8", label: "0.6 – 0.8", range: { min: 0.6, max: 0.8 } },
  { key: "0.8_1.0", label: "0.8 – 1.0", range: { min: 0.8, max: 1.0 } },
];

export function StrategyBuilderModal({ open, onOpenChange }: Props) {
  const create = useCreateStrategy();

  const [name, setName] = useState("");
  const [isDefault, setIsDefault] = useState(false);
  const [ageKey, setAgeKey] = useState("all");
  const [riskKey, setRiskKey] = useState("all");
  const [split, setSplit] = useState(0.5);
  const [aType, setAType] = useState<"sms" | "call">("sms");
  const [bType, setBType] = useState<"sms" | "call">("call");
  const [aDays, setADays] = useState<string>("-1");
  const [bDays, setBDays] = useState<string>("-1");

  const onSubmit = async () => {
    const age = AGE_BUCKETS.find((x) => x.key === ageKey)?.range;
    const risk = RISK_BUCKETS.find((x) => x.key === riskKey)?.range;
    const segment =
      isDefault
        ? null
        : {
            ...(age ? { age_min: age.min, age_max: age.max } : {}),
            ...(risk ? { risk_min: risk.min, risk_max: risk.max } : {}),
          };
    const parseDays = (s: string) =>
      s.split(",").map((x) => Number(x.trim())).filter((n) => Number.isFinite(n));

    await create.mutateAsync({
      name,
      is_default: isDefault,
      segment,
      ab: {
        split,
        A: { type: aType, days_of_action: parseDays(aDays) },
        B: { type: bType, days_of_action: parseDays(bDays) },
      },
      // id is server-generated
    } as any);

    onOpenChange(false);
    // reset
    setName(""); setIsDefault(false); setAgeKey("all"); setRiskKey("all");
    setSplit(0.5); setAType("sms"); setBType("call"); setADays("-1"); setBDays("-1");
  };

  return (
    <Dialog open={open} onOpenChange={onOpenChange}>
      <DialogContent className="rounded-2xl max-w-lg">
        <DialogHeader>
          <DialogTitle>Strategy Builder</DialogTitle>
        </DialogHeader>

        <div className="space-y-3">
          <div>
            <Label>Name</Label>
            <Input value={name} onChange={(e) => setName(e.target.value)} placeholder="e.g., Young High Risk Outreach" />
          </div>

          <div className="grid grid-cols-2 gap-3">
            <div>
              <Label>Age group</Label>
              <Select value={ageKey} onValueChange={setAgeKey}>
                <SelectTrigger><SelectValue placeholder="Select age group" /></SelectTrigger>
                <SelectContent>
                  {AGE_BUCKETS.map((b) => <SelectItem key={b.key} value={b.key}>{b.label}</SelectItem>)}
                </SelectContent>
              </Select>
            </div>
            <div>
              <Label>Risk group</Label>
              <Select value={riskKey} onValueChange={setRiskKey}>
                <SelectTrigger><SelectValue placeholder="Select risk group" /></SelectTrigger>
                <SelectContent>
                  {RISK_BUCKETS.map((b) => <SelectItem key={b.key} value={b.key}>{b.label}</SelectItem>)}
                </SelectContent>
              </Select>
            </div>
          </div>

          <div>
            <Label>A/B Split (A fraction)</Label>
            <Input type="number" min={0} max={1} step={0.05} value={split} onChange={(e) => setSplit(Number(e.target.value))} />
          </div>

          <div className="grid grid-cols-2 gap-3">
            <div>
              <Label>Variant A Type</Label>
              <Select value={aType} onValueChange={(v) => setAType(v as any)}>
                <SelectTrigger><SelectValue /></SelectTrigger>
                <SelectContent>
                  <SelectItem value="sms">SMS</SelectItem>
                  <SelectItem value="call">Call</SelectItem>
                </SelectContent>
              </Select>
            </div>
            <div>
              <Label>Variant B Type</Label>
              <Select value={bType} onValueChange={(v) => setBType(v as any)}>
                <SelectTrigger><SelectValue /></SelectTrigger>
                <SelectContent>
                  <SelectItem value="sms">SMS</SelectItem>
                  <SelectItem value="call">Call</SelectItem>
                </SelectContent>
              </Select>
            </div>
          </div>

          <div className="grid grid-cols-2 gap-3">
            <div>
              <Label>Variant A Days (comma-sep offsets)</Label>
              <Input value={aDays} onChange={(e) => setADays(e.target.value)} placeholder="-1,-2" />
            </div>
            <div>
              <Label>Variant B Days (comma-sep offsets)</Label>
              <Input value={bDays} onChange={(e) => setBDays(e.target.value)} placeholder="-1,-2" />
            </div>
          </div>

          <div className="flex items-center gap-2">
            <input id="def" type="checkbox" className="h-4 w-4" checked={isDefault} onChange={(e) => setIsDefault(e.target.checked)} />
            <Label htmlFor="def">Default strategy (applies to unmatched)</Label>
          </div>

          <div className="pt-2 flex justify-end gap-2">
            <Button variant="outline" onClick={() => onOpenChange(false)}>Cancel</Button>
            <Button onClick={onSubmit} disabled={!name || create.isPending}>Create</Button>
          </div>
        </div>
      </DialogContent>
    </Dialog>
  );
}