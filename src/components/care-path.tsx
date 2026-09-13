import {CalendarCheck2,MessageCircle,Stethoscope,ArrowDown} from "lucide-react";

export function CarePath() {
  return <div className="care-path" aria-hidden="true">
    <div className="path-heading">YOUR PATH TO CARE</div>
    <div className="path-step path-doctor"><span className="path-icon"><Stethoscope size={24}/></span><div><strong>Find your doctor</strong><small>The right expertise</small></div><span className="path-number">01</span></div>
    <span className="path-connector"><ArrowDown size={17}/></span>
    <div className="path-step path-booking"><span className="path-icon"><CalendarCheck2 size={24}/></span><div><strong>Plan your visit</strong><small>A time that works for you</small></div><span className="path-number">02</span></div>
    <span className="path-connector"><ArrowDown size={17}/></span>
    <div className="path-step path-followup"><span className="path-icon"><MessageCircle size={24}/></span><div><strong>Stay connected</strong><small>Keep your care in one place</small></div><span className="path-number">03</span></div>
  </div>;
}
