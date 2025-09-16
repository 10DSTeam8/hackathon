import { useState } from "react";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Label } from "@/components/ui/label";
import { Input } from "@/components/ui/input";
import { Toaster } from "@/components/ui/sonner";
import { toast } from "sonner";
import { ModeToggle } from "@/components/ui/mode-toggle";

export default function App() {
  const [name, setName] = useState("");

  return (
    <main className="min-h-screen bg-background text-foreground antialiased p-6">
      <header className="flex items-center justify-between max-w-3xl mx-auto">
        <ModeToggle />
      </header>

      <div className="mx-auto w-full max-w-md">
        <Card className="rounded-2xl shadow">
          <CardHeader>
            <CardTitle className="text-xl">shadcn/ui on Vite + Tailwind</CardTitle>
          </CardHeader>
          <CardContent className="space-y-4">
            <div className="space-y-2">
              <Label htmlFor="name">Your name</Label>
              <Input id="name" value={name} onChange={(e) => setName(e.target.value)} placeholder="Ada Lovelace" />
            </div>

            <Button
              onClick={() => {
                toast?.success?.(`Hi ${name || "there"}!`);
                // alert(`Hi ${name || "there"}!`);
              }}
            >
              Say hi
            </Button>
          </CardContent>
        </Card>
      </div>
      <Toaster />
    </main>
  );
}

