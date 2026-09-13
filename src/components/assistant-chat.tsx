"use client";

import Link from "next/link";
import {useRef,useState} from "react";
import type {FormEvent} from "react";
import {ArrowRight,ArrowUpRight,Apple,BotMessageSquare,CalendarDays,Hospital,Info,MessageSquarePlus,Send,Stethoscope,UserRound} from "lucide-react";

type Destination = {href:string;label:string};
type Message = {role:"user"|"assistant";text:string;links?:Destination[]};
const suggestions = [
  {title:"Find a doctor",detail:"Search by specialty and location",icon:Stethoscope,prompt:"Help me find a doctor"},
  {title:"Explore hospitals",detail:"Find facilities and services",icon:Hospital,prompt:"Help me find a hospital"},
  {title:"Plan a visit",detail:"See my appointments",icon:CalendarDays,prompt:"Help me manage my appointments"},
  {title:"Nutrition support",detail:"Explore everyday wellbeing",icon:Apple,prompt:"Show me nutrition support"},
];

// Explicitly a local interaction preview, not a model response or medical triage.
function previewResponse(text:string):Message {
  if (/emergency|urgent|chest pain|breath|bleeding|suicid/i.test(text)) return {role:"assistant",text:"This preview cannot assess urgent symptoms. Use emergency support for urgent help.",links:[{href:"/emergency",label:"Open emergency support"}]};
  if (/hospital|facility|facilities/i.test(text)) return {role:"assistant",text:"Explore the hospital directory to compare locations and available services. Listings in this demo are fictional.",links:[{href:"/hospitals",label:"Explore hospitals"}]};
  if (/appointment|visit|booking/i.test(text)) return {role:"assistant",text:"You can review existing appointments or find a doctor to book a new visit.",links:[{href:"/appointments",label:"My appointments"},{href:"/doctors",label:"Book a new visit"}]};
  if (/nutrition|food|eat|diet/i.test(text)) return {role:"assistant",text:"Explore the nutrition section for wellbeing and recovery support.",links:[{href:"/nutrition",label:"Explore nutrition"}]};
  if (/pharmac|medicine|prescription/i.test(text)) return {role:"assistant",text:"Choose whether to review prescription details or explore the pharmacy directory.",links:[{href:"/prescriptions",label:"My prescriptions"},{href:"/pharmacy",label:"Find a pharmacy"}]};
  if (/doctor|specialist|dermatolog|cardiolog|pediatr|general physician/i.test(text)) {
    const specialty = /dermatolog/i.test(text)?"Dermatology":/cardiolog/i.test(text)?"Cardiology":/pediatr/i.test(text)?"Pediatrics":"";
    const city = ["Awka","Lagos","Abuja","Enugu","Onitsha","Port Harcourt"].find(city=>text.toLowerCase().includes(city.toLowerCase()));
    const params = new URLSearchParams();
    if (specialty) params.set("specialty",specialty);
    if (city) params.set("city",city);
    return {role:"assistant",text:"Start with the doctor directory. You can compare specialties, locations, and fees, then view available appointment times.",links:[{href:"/doctors"+(params.size?"?"+params.toString():""),label:specialty?"Explore "+specialty.toLowerCase():"Find a doctor"}]};
  }
  return {role:"assistant",text:"This interactive preview can help you open a care service. Live AI answers aren’t connected yet. Try finding a doctor, exploring hospitals, or managing a visit.",links:[{href:"/doctors",label:"Find a doctor"},{href:"/hospitals",label:"Explore hospitals"}]};
}

export function AssistantChat({intent}:{intent?:string}) {
  const initialPrompt = intent==="doctor"?"Help me find a doctor":intent==="hospital"?"Help me find a hospital":undefined;
  const [messages,setMessages] = useState<Message[]>(initialPrompt?[{role:"user",text:initialPrompt},previewResponse(initialPrompt)]:[]);
  const [draft,setDraft] = useState("");
  const input = useRef<HTMLInputElement>(null);
  function send(text:string) {
    const value = text.trim();
    if (!value) return;
    setMessages(previous=>[...previous,{role:"user",text:value},previewResponse(value)]);
    setDraft("");
    input.current?.focus();
  }
  function submit(event:FormEvent<HTMLFormElement>) {event.preventDefault();send(draft)}
  return <div className="page assistant-page">
    <header className="assistant-page-header"><div className="assistant-title"><span className="assistant-icon"><BotMessageSquare size={29}/></span><div><h1>Fuuud AI <span className="preview-tag">Preview</span></h1><p>Your care-navigation assistant</p></div></div><button className="new-chat" onClick={()=>{setMessages([]);setDraft("");input.current?.focus()}}><MessageSquarePlus size={19}/><span>New chat</span></button></header>
    <div className="assistant-preview-note"><Info size={16}/><p>Interactive preview · Live AI replies are not connected. You can explore care services below.</p></div>
    <section className="chat-workspace" aria-label="Care assistant">
      {messages.length===0 ? <div className="chat-welcome">
        <span className="chat-welcome-icon"><BotMessageSquare size={40} strokeWidth={1.6}/></span>
        <p className="eyebrow">LET’S START WITH YOU</p><h2>What can I help<br/>you find today?</h2><p>Doctors, hospitals, or your next appointment.<br/>Choose a starting point, or type below.</p>
        <div className="chat-suggestions">{suggestions.map(suggestion=><button key={suggestion.title} onClick={()=>send(suggestion.prompt)}><suggestion.icon size={23}/><span><strong>{suggestion.title}</strong><small>{suggestion.detail}</small></span><ArrowUpRight size={17}/></button>)}</div>
      </div> : <div className="chat-messages" role="log" aria-label="Conversation" aria-live="polite" aria-relevant="additions">{messages.map((message,index)=><article key={index} className={"chat-message "+message.role}><span className="message-avatar">{message.role==="assistant"?<BotMessageSquare size={21}/>:<UserRound size={19}/>}</span><div className="message-content"><span className="message-author">{message.role==="assistant"?"Fuuud · Preview":"You"}</span><p>{message.text}</p>{message.links&&<div className="message-actions">{message.links.map(link=><Link href={link.href} key={link.href}>{link.label}<ArrowRight size={17}/></Link>)}</div>}</div></article>)}</div>}
      <form onSubmit={submit} className="chat-composer"><label className="sr-only" htmlFor="assistant-message">Message Fuuud AI</label><input id="assistant-message" ref={input} value={draft} onChange={event=>setDraft(event.target.value)} placeholder="What care are you looking for?" maxLength={500} autoComplete="off"/><button type="submit" disabled={!draft.trim()} aria-label="Send message"><Send size={20}/></button></form>
      <p className="chat-disclaimer">For finding services, not diagnosis. <Link href="/emergency">Need urgent help?</Link></p>
    </section>
  </div>;
}
