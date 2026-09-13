"use client";

import Link from "next/link";
import {useRouter} from "next/navigation";
import {FormEvent, useState} from "react";
import {Logo} from "./ui";

const destinationFor = (role: string) => role === "doctor" ? "/doctor" : role === "hospital_staff" ? "/hospital" : role === "admin" ? "/admin" : "/";

export function AuthForm({register = false}: {register?: boolean}) {
  const router = useRouter();
  const [error, setError] = useState("");
  const [busy, setBusy] = useState(false);

  async function submit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    setBusy(true);
    setError("");
    const payload = Object.fromEntries(new FormData(event.currentTarget));
    try {
      if (register) {
        const created = await fetch("/api/backend/auth/register", {method: "POST", headers: {"Content-Type": "application/json"}, body: JSON.stringify(payload)});
        const data = await created.json();
        if (!created.ok) throw new Error(data.detail);
        const query = data.verification_token ? `token=${encodeURIComponent(data.verification_token)}` : `email=${encodeURIComponent(String(payload.email))}`;
        router.push(`/verify-email?${query}`);
        return;
      }
      const login = await fetch("/api/backend/auth/login", {method: "POST", headers: {"Content-Type": "application/json"}, body: JSON.stringify({email: payload.email, password: payload.password})});
      const loginData = await login.json();
      if (!login.ok) throw new Error(loginData.detail);
      const me = await fetch("/api/backend/users/me");
      const user = await me.json();
      if (!me.ok) throw new Error(user.detail);
      router.push(destinationFor(user.role));
      router.refresh();
    } catch (caught) {
      setError(caught instanceof Error ? caught.message : "Something went wrong.");
    } finally {
      setBusy(false);
    }
  }

  return <div className="page auth-page">
    <div className="text-center"><Logo/><h1 className="text-3xl font-black mt-8">{register ? "Create your account" : "Welcome back"}</h1><p className="muted mt-2">{register ? "Choose the account that matches how you will use Fuuud." : "Continue your healthcare journey."}</p></div>
    <form onSubmit={submit} className="card p-6 mt-7 space-y-4">
      {register && <label className="block text-sm font-bold">Account type<select required name="role" defaultValue="patient" className="field mt-2"><option value="patient">Patient</option><option value="doctor">Doctor</option><option value="hospital_staff">Hospital staff</option></select></label>}
      {register && <div className="grid grid-cols-2 gap-2"><label className="text-sm font-bold">First name<input required name="first_name" className="field mt-2"/></label><label className="text-sm font-bold">Last name<input required name="last_name" className="field mt-2"/></label></div>}
      <label className="block text-sm font-bold">Email address<input required name="email" className="field mt-2" type="email" autoComplete="email" placeholder="you@example.com"/></label>
      <label className="block text-sm font-bold">Password<input required minLength={8} name="password" className="field mt-2" type="password" autoComplete={register ? "new-password" : "current-password"} placeholder="At least 8 characters"/></label>
      {error && <p className="rounded-xl bg-red-50 p-3 text-sm text-red-700" role="alert">{error}</p>}
      <button disabled={busy} className="btn btn-primary w-full">{busy ? "Please wait..." : register ? "Create account" : "Log in"}</button>
      {!register && <p className="text-center text-sm"><Link className="font-bold text-green-700" href="/forgot-password">Forgot your password?</Link></p>}
      {register && <p className="muted text-xs text-center">Doctor and hospital staff accounts require verification before provider tools are activated.</p>}
      <p className="muted text-xs text-center">Your next step toward more connected care.</p>
    </form>
    <p className="text-center text-sm mt-5">{register ? "Already registered?" : "New to Fuuud?"} <Link className="font-bold text-green-700" href={register ? "/login" : "/register"}>{register ? "Log in" : "Create account"}</Link></p>
  </div>;
}
