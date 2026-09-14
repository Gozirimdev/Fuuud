"use client";

import Image from "next/image";
import {useState} from "react";
import {Pause,Play} from "lucide-react";

export function CarePath() {
  const [paused,setPaused]=useState(false);
  return <figure className="care-editorial" data-paused={paused}>
    <div className="care-photo-wrap"><Image className="care-photo" src="/images/care-consultation.webp" alt="Illustrative scene of a doctor listening attentively to a patient in a sunlit clinic." fill sizes="(max-width: 600px) 100vw, (max-width: 1000px) 50vw, 45vw" preload/></div>
    <figcaption className="care-photo-caption"><p>Good care starts<br/>with being heard.</p><button type="button" className="care-motion-toggle" onClick={()=>setPaused(!paused)} aria-label={paused?"Play photo animation":"Pause photo animation"}>{paused?<Play size={14}/>:<Pause size={14}/>}</button></figcaption>
  </figure>;
}
