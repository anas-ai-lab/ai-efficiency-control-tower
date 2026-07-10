"use client";

import { useRouter } from "next/navigation";
import { useState } from "react";

import { login } from "@/app/actions";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";

// Minimaler Admin-Login (V4-P-Auth, nur funktional -- Design folgt in V4-P8).
// Bei Erfolg setzt die login()-Server-Action das httpOnly-Session-Cookie; ein
// router.refresh() laesst die Server-Komponenten (Nav, gated Pages) den neuen
// Auth-Zustand neu auswerten.
export function LoginForm() {
  const router = useRouter();
  const [password, setPassword] = useState("");
  const [pending, setPending] = useState(false);
  const [error, setError] = useState<string | null>(null);

  async function handleSubmit(e: React.FormEvent) {
    e.preventDefault();
    if (password.length === 0) return;
    setPending(true);
    setError(null);
    const result = await login(password);
    if (result.ok) {
      setPassword("");
      router.push("/");
      router.refresh();
      return;
    }
    setError(result.error ?? "Login fehlgeschlagen.");
    setPending(false);
  }

  return (
    <form onSubmit={handleSubmit} className="space-y-4">
      <div className="space-y-1.5">
        <Label htmlFor="admin-password">Admin-Passwort</Label>
        <Input
          id="admin-password"
          type="password"
          autoComplete="current-password"
          value={password}
          onChange={(e) => setPassword(e.target.value)}
          disabled={pending}
          autoFocus
        />
      </div>
      {error !== null && (
        <p
          role="alert"
          className="rounded-lg border border-destructive/25 bg-destructive/5 px-4 py-3 text-sm text-destructive"
        >
          {error}
        </p>
      )}
      <Button type="submit" disabled={pending || password.length === 0}>
        {pending ? "Anmelden …" : "Anmelden"}
      </Button>
    </form>
  );
}

export default LoginForm;
