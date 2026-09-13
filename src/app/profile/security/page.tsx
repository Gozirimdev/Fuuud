import {cookies} from "next/headers";
import {redirect} from "next/navigation";
import {CheckCircle2,KeyRound,LogIn,MailCheck,RotateCcw,ShieldCheck,UserPlus} from "lucide-react";
import {PageHeader} from "@/components/ui";
import {getMyAuditEvents} from "@/lib/api";

const details={"account.registered":{label:"Account created",icon:UserPlus},"account.login":{label:"Signed in",icon:LogIn},"password.reset_requested":{label:"Password reset requested",icon:RotateCcw},"password.reset_completed":{label:"Password changed",icon:KeyRound},"email.verification_requested":{label:"Email verification requested",icon:MailCheck},"email.verified":{label:"Email address verified",icon:CheckCircle2}};

export default async function SecurityActivity(){const token=(await cookies()).get("fuuud_session")?.value;if(!token)redirect("/login?next=/profile/security");let events;try{events=await getMyAuditEvents(token)}catch{redirect("/login")};return <div className="page"><PageHeader title="Security activity" subtitle="Recent access and security changes on your account." back="/profile"/><section className="card divide-y">{events.map(event=>{const detail=details[event.event_type as keyof typeof details]??{label:event.event_type,icon:ShieldCheck};const Icon=detail.icon;return <article className="flex items-center gap-4 p-4" key={event.id}><span className="grid h-10 w-10 shrink-0 place-items-center rounded-full bg-green-50 text-green-700"><Icon size={18}/></span><div><h2 className="text-sm font-bold">{detail.label}</h2><time className="muted text-xs" dateTime={event.created_at}>{new Intl.DateTimeFormat("en-NG",{dateStyle:"medium",timeStyle:"short"}).format(new Date(event.created_at))}</time></div></article>})}</section></div>}
