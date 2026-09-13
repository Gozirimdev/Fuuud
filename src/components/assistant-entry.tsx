import Link from "next/link";
import {ArrowRight,BotMessageSquare,Hospital,Stethoscope} from "lucide-react";

export function AssistantEntry() {
  return <section className="assistant-entry" aria-labelledby="assistant-entry-title">
    <div className="assistant-entry-top">
      <span className="assistant-icon"><BotMessageSquare size={29}/></span>
      <div className="assistant-entry-copy"><div className="assistant-label">Fuuud AI <span className="preview-tag">Preview</span></div><h2 id="assistant-entry-title">A question is a good place to start.</h2><p>Tell the assistant what kind of care you’re looking for.</p></div>
      <Link className="assistant-open" href="/agent" aria-label="Open Fuuud AI assistant"><ArrowRight size={22}/></Link>
    </div>
    <div className="assistant-prompts"><Link href="/agent?intent=doctor"><Stethoscope size={17}/>Help me find a doctor<ArrowRight size={14}/></Link><Link href="/agent?intent=hospital"><Hospital size={17}/>Find a hospital<ArrowRight size={14}/></Link></div>
  </section>;
}
