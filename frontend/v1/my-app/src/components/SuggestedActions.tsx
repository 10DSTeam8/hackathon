import type { AppointmentSummary } from "@/api/types";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { useSendSMS, useCallNow } from "@/api/hooks";

function shouldSuggestSMS(a: AppointmentSummary) {
  const high = a.live_adjusted_risk >= 0.4;
  return high;
}
function shouldSuggestCall(a: AppointmentSummary) {
  const veryHigh = a.live_adjusted_risk >= 0.6;
  return veryHigh;
}

export function SuggestedActions({ rows }: { rows: AppointmentSummary[] }) {
  const sms = useSendSMS();
  const call = useCallNow();

  const candidates = rows.filter((r) => shouldSuggestSMS(r) || shouldSuggestCall(r));

  return (
    <Card className="rounded-2xl h-full">
      <CardHeader className="pb-2">
        <CardTitle>Suggested Actions (Today)</CardTitle>
      </CardHeader>
      <CardContent className="pt-0 space-y-2">
        {candidates.length === 0 ? (
          <p className="text-sm opacity-70">No urgent actions right now.</p>
        ) : (
          candidates.slice(0, 6).map((r) => (
            <div key={r.id} className="flex items-center justify-between rounded-lg border p-2">
              <div className="text-sm">
                <div className="font-medium">{r.patient.name}</div>
                <div className="opacity-70">Live risk {(r.live_adjusted_risk * 100).toFixed(0)}% • {r.time}</div>
              </div>
              <div className="flex gap-2">
                <Button
                  size="sm"
                  variant="secondary"
                  onClick={() =>
                    sms.mutate({ appointment_id: r.id, template: "Hi {{name}}, reply YES to confirm" })
                  }
                >
                  Send SMS
                </Button>
                {shouldSuggestCall(r) && (
                  <Button size="sm" onClick={() => call.mutate(r.id)}>
                    Call
                  </Button>
                )}
              </div>
            </div>
          ))
        )}
      </CardContent>
    </Card>
  );
}