"use client";

import Link from "next/link";
import {FormEvent, useState} from "react";
import {CheckCircle2, LoaderCircle, MailCheck} from "lucide-react";
import {Logo} from "./ui";

export function EmailVerification({token, email}: {token: string; email: string}) {
  const [busy, setBusy] = useState(false);
  const [verified, setVerified] = useState(false);
  const [error, setError] = useState(false);
  const [address, setAddress] = useState(email);
  const [newToken, setNewToken] = useState("");
  const [message, setMessage] = useState(token
    ? "Confirm below to verify your email address."
    : "Check your inbox for a verification link. You can request another link below.");

  async function request(verify: boolean) {
    setBusy(true);
    setError(false);
    setNewToken("");
    try {
      const response = await fetch(`/api/backend/auth/email-verification/${verify ? "verify" : "request"}`, {
        method: "POST",
        headers: {"Content-Type": "application/json"},
        body: JSON.stringify(verify ? {token} : {email: address}),
      });
      const data = await response.json();
      if (!response.ok) throw new Error(typeof data.detail === "string" ? data.detail : "Check your details and try again.");
      setVerified(verify);
      setMessage(data.message);
      setNewToken(data.verification_token || "");
    } catch (caught) {
      setError(true);
      setMessage(caught instanceof Error ? caught.message : "Could not complete the request. Please try again.");
    } finally {
      setBusy(false);
    }
  }

  function resend(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    void request(false);
  }

  return <div className="page max-w-md md:!ml-auto"><div className="text-center">
    <Logo/>
    <div className="card mt-8 p-7">
      {busy ? <LoaderCircle className="mx-auto animate-spin text-green-600" size={38}/>
        : verified ? <CheckCircle2 className="mx-auto text-green-600" size={38}/>
          : <MailCheck className={`mx-auto ${error ? "text-red-500" : "text-green-600"}`} size={38}/>}
      <h1 className="mt-4 text-2xl font-black">{verified ? "Email verified" : "Verify your email"}</h1>
      <p className="muted mt-2 text-sm leading-6" role={error ? "alert" : "status"}>{message}</p>
      {verified ? <Link className="btn btn-primary mt-6 w-full" href="/login">Continue to login</Link> : <>
        {token && <button type="button" disabled={busy} onClick={() => void request(true)} className="btn btn-primary mt-6 w-full">Verify email address</button>}
        <form onSubmit={resend} className="mt-6 text-left">
          <label className="block text-sm font-bold" htmlFor="verification-email">Email address</label>
          <input id="verification-email" type="email" required autoComplete="email" className="field mt-2" value={address} onChange={event => setAddress(event.target.value)} placeholder="you@example.com"/>
          <button type="submit" disabled={busy} className="btn btn-outline mt-3 w-full">Send another verification link</button>
          <p className="muted mt-2 text-xs">Allow a minute between requests and check your spam folder.</p>
        </form>
        {newToken && <Link className="btn btn-primary mt-6 w-full" href={`/verify-email?token=${encodeURIComponent(newToken)}`}>Open verification link</Link>}
        <Link className="btn btn-outline mt-4 w-full" href="/login">Back to login</Link>
      </>}
    </div>
  </div></div>;
}
