import Link from "next/link";
import {cookies} from "next/headers";
import {ArrowRight,ArrowUpRight,Apple,Hospital,CalendarDays,CalendarPlus,ChevronRight,FileText,UserRound,MessageCircle,Store,Search,Siren,Stethoscope} from "lucide-react";
import {getCurrentUser,getMyAppointments} from "@/lib/api";
import {CarePath} from "@/components/care-path";
import {AssistantEntry} from "@/components/assistant-entry";
import type {ApiAppointment} from "@/lib/api/types";
const services=[
 {href:"/doctors",title:"Find a doctor",text:"The right specialist for you",icon:Stethoscope,tone:"mint"},
 {href:"/hospitals",title:"Explore hospitals",text:"Know where to find care",icon:Hospital,tone:"lavender"},
 {href:"/pharmacy",title:"Find a pharmacy",text:"Your next stop for medicines",icon:Store,tone:"peach"},
 {href:"/nutrition",title:"Eat well, feel better",text:"Support your everyday wellbeing",icon:Apple,tone:"butter"}
];
export default async function Home(){
 const token=(await cookies()).get("fuuud_session")?.value;
 let firstName="there",signedIn=false;
 let appointments:ApiAppointment[]|null=null;
 if(token){const [user,care]=await Promise.allSettled([getCurrentUser(token),getMyAppointments(token,"upcoming")]);if(user.status==="fulfilled"){firstName=user.value.first_name;signedIn=true}if(care.status==="fulfilled")appointments=care.value}
 const next=appointments?.slice().sort((a,b)=>Date.parse(a.scheduled_at)-Date.parse(b.scheduled_at))[0];
 const showAppointments=!!next||(signedIn&&appointments===null);
 return <div className="page home-page">
 <header className="dashboard-header"><div><p className="eyebrow">YOUR EVERYDAY CARE COMPANION</p><h1>Hello, {firstName}<span className="greeting-dot">.</span></h1><p>Let’s make a little room for your wellbeing.</p></div><Link href={signedIn?"/profile":"/login"} className="account-link"><span className="account-avatar">{signedIn?firstName.slice(0,1).toUpperCase():<UserRound size={20}/>}</span><span>{signedIn?"My account":"Sign in"}</span><ChevronRight size={16}/></Link></header>
 <section className="care-hero" aria-labelledby="hero-title"><div className="hero-copy"><h2 id="hero-title">Your health.<br/>Your pace.<br/><em>Your kind of care.</em></h2><p>Find a doctor who understands you, plan your next visit, and make room for feeling better.</p><div className="hero-actions"><Link className="btn hero-button" href="/doctors">Find a doctor <ArrowUpRight size={18}/></Link><Link className="hero-secondary" href="/hospitals">Explore hospitals <ArrowRight size={16}/></Link></div><div className="hero-footnote"><span/> Doctors, appointments, and everyday wellbeing.</div></div><CarePath/></section>
 <nav className="care-journey" aria-label="Explore your care journey"><Link href="/doctors"><span className="care-journey-number">01</span><span><strong>Find your care</strong><small>Explore doctors & specialties</small></span><ArrowUpRight size={17}/></Link><Link href="/appointments"><span className="care-journey-number">02</span><span><strong>Make a little time</strong><small>Plan your next appointment</small></span><ArrowUpRight size={17}/></Link><Link href="/nutrition"><span className="care-journey-number">03</span><span><strong>Feel better, every day</strong><small>Support your wellbeing</small></span><ArrowUpRight size={17}/></Link></nav>
 <div className="home-columns"><div className="home-main">
 <form action="/doctors" className="home-search" role="search"><Search size={21}/><label className="sr-only" htmlFor="care-search">Search doctors by name or specialty</label><input id="care-search" name="search" placeholder="Find a doctor or specialty…"/><button type="submit" aria-label="Search doctors"><ArrowRight size={20}/></button></form>
 <AssistantEntry/>
 <section className="services-section" aria-labelledby="services-title"><div className="section-heading"><div><p className="eyebrow">ONE SMALL STEP</p><h2 id="services-title">What brings you here?</h2></div><span className="section-note">Care, on your terms</span></div><div className="service-grid">{services.map(service=><Link href={service.href} className={"service-card "+service.tone} key={service.href}><div className="service-card-top"><span className="service-icon"><service.icon size={23} strokeWidth={1.6}/></span><ArrowUpRight className="service-arrow" size={19}/></div><h3>{service.title}</h3><p>{service.text}</p></Link>)}</div></section>

 <p className="demo-note">You’re exploring a demo. Provider listings are fictional; appointment booking uses the connected service.</p>
 </div><aside className="home-rail" aria-label="Your care and quick links">
 <section className="care-panel"><div className="section-heading"><h2>Your next step</h2><CalendarDays size={19}/></div><div className="appointment-illustration" aria-hidden="true"><CalendarDays size={32} strokeWidth={1.4}/><span><CalendarPlus size={14}/></span></div><p className="eyebrow">{next?"COMING UP":"A LITTLE PLANNING, MORE PEACE OF MIND"}</p><h3>{next?"Dr. "+next.practitioner.first_name+" "+next.practitioner.last_name:signedIn?appointments===null?"Your care, in one place":"Make time for you":"Your care starts here"}</h3><p>{next?new Date(next.scheduled_at).toLocaleString("en-NG",{dateStyle:"medium",timeStyle:"short",timeZone:"Africa/Lagos"})+" (WAT)":signedIn?appointments===null?"Open your appointments to check your latest bookings.":"No upcoming appointments. Find a doctor whenever you’re ready.":"Sign in to keep track of your appointments and plan your next visit."}</p><Link className="btn btn-primary" href={showAppointments?"/appointments":signedIn?"/doctors":"/login"}>{showAppointments?"View appointments":signedIn?"Find a doctor":"Sign in to your account"}<ArrowRight size={16}/></Link></section>
 <section className="quick-panel"><h2>Keep your care connected</h2><Link href="/appointments"><span className="quick-icon"><CalendarDays size={18}/></span><span>My appointments<small>Plan and review your visits</small></span><ChevronRight size={16}/></Link><Link href="/prescriptions"><span className="quick-icon"><FileText size={18}/></span><span>Prescriptions<small>Review your medicine details</small></span><ChevronRight size={16}/></Link><Link href="/messages"><span className="quick-icon"><MessageCircle size={18}/></span><span>Messages<small>Continue the conversation</small></span><ChevronRight size={16}/></Link></section>
 <Link href="/emergency" className="urgent-card"><Siren size={22}/><div><h2>Need urgent help?</h2><p>Go straight to emergency support.</p></div><ArrowUpRight size={18}/></Link>
 </aside></div></div>;
}
