"use client";

import Link from "next/link";
import {usePathname} from "next/navigation";
import {Apple,ArrowUpRight,BotMessageSquare,CalendarDays,FileText,Home,Hospital,LayoutDashboard,MessageCircle,Settings,ShieldCheck,Siren,Stethoscope,Store,UserRound} from "lucide-react";
import {Logo} from "./ui";

const patientNav = [
  {h:"/",l:"Overview",i:Home},
  {h:"/doctors",l:"Find a doctor",i:Stethoscope},
  {h:"/hospitals",l:"Hospitals",i:Hospital},
  {h:"/messages",l:"Messages",i:MessageCircle},
  {h:"/profile",l:"My account",i:UserRound},
];
const mobilePatientNav = [
  {h:"/",l:"Home",i:Home},
  {h:"/doctors",l:"Doctors",i:Stethoscope},
  {h:"/agent",l:"Fuuud AI",i:BotMessageSquare},
  {h:"/messages",l:"Messages",i:MessageCircle},
  {h:"/hospitals",l:"Hospitals",i:Hospital},
];
const careNav = [
  {h:"/appointments",l:"Appointments",i:CalendarDays},
  {h:"/prescriptions",l:"Prescriptions",i:FileText},
  {h:"/pharmacy",l:"Pharmacies",i:Store},
  {h:"/nutrition",l:"Nutrition",i:Apple},
];
const workspaceNav = {
  doctor:[{h:"/doctor",l:"Workspace",i:LayoutDashboard},{h:"/profile",l:"Account",i:UserRound}],
  hospital:[{h:"/hospital",l:"Workspace",i:LayoutDashboard},{h:"/profile",l:"Account",i:UserRound}],
  admin:[{h:"/admin",l:"Administration",i:ShieldCheck},{h:"/profile",l:"Account",i:Settings}],
};
const publicRoutes = ["/login","/register","/forgot-password","/reset-password","/verify-email","/onboarding"];
type NavItem = (typeof patientNav)[number];

function NavLink({item}:{item:NavItem}) {
  const pathname = usePathname();
  const active = pathname === item.h || (item.h !== "/" && pathname.startsWith(item.h + "/"));
  return <Link href={item.h} className={["nav-link",active?"is-active":"",item.h==="/agent"?"nav-ai":""].join(" ")} aria-current={active?"page":undefined}>
    <span className="nav-icon"><item.i size={21} strokeWidth={1.9}/></span><span>{item.l}</span>
  </Link>;
}

export function Shell({children}:{children:React.ReactNode}) {
  const pathname = usePathname();
  if (publicRoutes.includes(pathname)) return <main id="main-content" className="public-shell">{children}</main>;
  const isRoute = (route:string) => pathname === route || pathname.startsWith(route + "/");
  const workspace = isRoute("/doctor")?"doctor":isRoute("/hospital")?"hospital":isRoute("/admin")?"admin":null;
  const primary = workspace ? workspaceNav[workspace] : patientNav;
  return <>
    <a href="#main-content" className="skip-link">Skip to content</a>
    <aside className="desktop-sidebar">
      <div className="sidebar-brand"><Logo/><span>CARE, CLOSER.</span></div>
      <nav aria-label="Main navigation"><p className="nav-caption">Your space</p>{primary.map(item=><NavLink key={item.h} item={item}/>)}
        {!workspace && <><p className="nav-caption">Your care</p>{careNav.map(item=><NavLink key={item.h} item={item}/>)}</>}
      </nav>
      {!workspace && <Link href="/agent" className="sidebar-guide" aria-current={isRoute("/agent")?"page":undefined}>
        <span className="assistant-icon"><BotMessageSquare size={25}/></span>
        <strong>Meet Fuuud AI <span className="preview-tag">Preview</span></strong>
        <p>Your starting point for finding care.</p><span className="sidebar-guide-cta">Open assistant <ArrowUpRight size={17}/></span>
      </Link>}
      <Link href="/emergency" className="sidebar-emergency"><Siren size={19}/>Emergency help<ArrowUpRight size={16}/></Link>
    </aside>
    <header className="mobile-header"><Logo/><div className="mobile-header-actions"><Link href="/emergency" className="urgent-link"><Siren size={18}/><span>Urgent help</span></Link><Link href="/profile" className="header-account" aria-label="My account"><UserRound size={21}/></Link></div></header>
    <main id="main-content" className="app-content">{children}</main>
    <nav className="mobile-nav" aria-label="Mobile navigation">{(workspace?primary:mobilePatientNav).map(item=><NavLink key={item.h} item={item}/>)}</nav>
  </>;
}
