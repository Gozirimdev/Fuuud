"use client";

import Link from "next/link";
import {useRef,useState} from "react";
import type {FormEvent} from "react";
import {ArrowRight,ArrowUpRight,Apple,BotMessageSquare,CalendarDays,Hospital,Send,Stethoscope,UserRound,Loader2} from "lucide-react";

type Message = {role:"user"|"assistant";text:string;};
const suggestions = [
  {title:"Find a doctor",detail:"Search by specialty and location",icon:Stethoscope,prompt:"Help me find a doctor"},
  {title:"Explore hospitals",detail:"Find facilities and services",icon:Hospital,prompt:"Help me find a hospital"},
  {title:"Plan a visit",detail:"See my appointments",icon:CalendarDays,prompt:"Help me manage my appointments"},
  {title:"Nutrition support",detail:"Explore everyday wellbeing",icon:Apple,prompt:"Show me nutrition support"},
];

export function AssistantChat({intent}:{intent?:string}) {
  const initialPrompt = intent==="doctor"?"Help me find a doctor":intent==="hospital"?"Help me find a hospital":undefined;
  const [messages,setMessages] = useState<Message[]>([]);
  const [draft,setDraft] = useState("");
  const [isLoading,setIsLoading] = useState(false);
  const [error,setError] = useState<string|null>(null);
  const input = useRef<HTMLInputElement>(null);
  const messagesEndRef = useRef<HTMLDivElement>(null);

  // Auto-send initial prompt
  useState(()=>{
    if (initialPrompt) {
      setTimeout(()=>send(initialPrompt),100);
    }
  });

  // Auto-scroll to bottom
  useState(()=>{
    messagesEndRef.current?.scrollIntoView({behavior:"smooth"});
  });

  async function send(text:string) {
    const value = text.trim();
    if (!value || isLoading) return;

    const userMessage:Message = {role:"user",text:value};
    setMessages(prev=>[...prev,userMessage]);
    setDraft("");
    setError(null);
    setIsLoading(true);

    try {
      // Build message history for API
      const conversationMessages = [...messages,userMessage].map(msg=>({
        role:msg.role,
        content:[{text:msg.text}]
      }));

      const response = await fetch('/api/agent',{
        method:'POST',
        headers:{'Content-Type':'application/json'},
        body:JSON.stringify({messages:conversationMessages})
      });

      if (!response.ok) {
        const errorData = await response.json().catch(()=>({}));
        const errorMsg = errorData.errorCode
          ? `${errorData.error} (${errorData.errorCode})`
          : (errorData.error || 'Failed to get response');
        throw new Error(errorMsg);
      }

      const data = await response.json();

      // Handle emergency detection
      if (data.emergencyDetected) {
        setMessages(prev=>[...prev,{role:"assistant",text:data.content[0].text}]);
        setIsLoading(false);
        return;
      }

      // Extract text from content blocks
      let responseText = '';
      if (data.content && Array.isArray(data.content)) {
        for (const block of data.content) {
          if (block.text) {
            responseText += block.text;
          }
        }
      }

      if (responseText) {
        setMessages(prev=>[...prev,{role:"assistant",text:responseText}]);
      } else {
        throw new Error('Empty response from AI');
      }

    } catch (err) {
      console.error('Agent error:',err);
      const errorMessage = err instanceof Error ? err.message : 'Something went wrong. Please try again.';
      setError(errorMessage);
      // Remove the user message if there was an error
      setMessages(prev=>prev.slice(0,-1));
    } finally {
      setIsLoading(false);
      input.current?.focus();
    }
  }

  function submit(event:FormEvent<HTMLFormElement>) {
    event.preventDefault();
    send(draft);
  }

  return <div className="page assistant-page">
    <header className="assistant-page-header">
      <div className="assistant-title">
        <span className="assistant-icon"><BotMessageSquare size={29}/></span>
        <div>
          <h1>Fuuud AI</h1>
          <p>Your care-navigation assistant</p>
        </div>
      </div>
    </header>

    <section className="chat-workspace" aria-label="Care assistant">
      {messages.length===0 && !isLoading ? <div className="chat-welcome">
        <span className="chat-welcome-icon"><BotMessageSquare size={40} strokeWidth={1.6}/></span>
        <p className="eyebrow">LET'S START WITH YOU</p>
        <h2>What can I help<br/>you find today?</h2>
        <p>Doctors, hospitals, or pharmacies near you.<br/>Choose a starting point, or type below.</p>
        <div className="chat-suggestions">
          {suggestions.map(suggestion=><button key={suggestion.title} onClick={()=>send(suggestion.prompt)} disabled={isLoading}>
            <suggestion.icon size={23}/>
            <span>
              <strong>{suggestion.title}</strong>
              <small>{suggestion.detail}</small>
            </span>
            <ArrowUpRight size={17}/>
          </button>)}
        </div>
      </div> : <div className="chat-messages" role="log" aria-label="Conversation" aria-live="polite" aria-relevant="additions">
        {messages.map((message,index)=><article key={index} className={"chat-message "+message.role}>
          <span className="message-avatar">
            {message.role==="assistant"?<BotMessageSquare size={21}/>:<UserRound size={19}/>}
          </span>
          <div className="message-content">
            <span className="message-author">{message.role==="assistant"?"Fuuud AI":"You"}</span>
            <p>{message.text}</p>
          </div>
        </article>)}

        {isLoading && <article className="chat-message assistant">
          <span className="message-avatar"><BotMessageSquare size={21}/></span>
          <div className="message-content">
            <span className="message-author">Fuuud AI</span>
            <p className="flex items-center gap-2 text-gray-500">
              <Loader2 size={16} className="animate-spin"/>
              Thinking...
            </p>
          </div>
        </article>}

        <div ref={messagesEndRef}/>
      </div>}

      {error && <div className="bg-red-50 border border-red-200 rounded-lg p-3 mx-4 mb-4 text-red-800 text-sm">
        {error}
      </div>}

      <form onSubmit={submit} className="chat-composer">
        <label className="sr-only" htmlFor="assistant-message">Message Fuuud AI</label>
        <input
          id="assistant-message"
          ref={input}
          value={draft}
          onChange={event=>setDraft(event.target.value)}
          placeholder="What care are you looking for?"
          maxLength={500}
          autoComplete="off"
          disabled={isLoading}
        />
        <button type="submit" disabled={!draft.trim() || isLoading} aria-label="Send message">
          <Send size={20}/>
        </button>
      </form>
      <p className="chat-disclaimer">
        For finding services, not diagnosis. Demo data only. <Link href="/emergency">Need urgent help?</Link>
      </p>
    </section>
  </div>;
}
