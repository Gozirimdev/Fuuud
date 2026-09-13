import {NextRequest,NextResponse} from "next/server";
const api=process.env.API_URL||process.env.NEXT_PUBLIC_API_URL||"http://localhost:8000";
async function proxy(req:NextRequest,{params}:{params:Promise<{path:string[]}>}){const {path}=await params;const token=req.cookies.get("fuuud_session")?.value;const body=["GET","HEAD"].includes(req.method)?undefined:await req.text();let upstream:Response;
 try{upstream=await fetch(`${api}/api/v1/${path.join("/")}${req.nextUrl.search}`,{method:req.method,body,headers:{"Content-Type":"application/json",...(token?{Authorization:`Bearer ${token}`}:{})},cache:"no-store"})}catch{return NextResponse.json({detail:"The healthcare service is unavailable. Please try again."},{status:503})}
 const data=await upstream.json().catch(()=>({}));const response=NextResponse.json(data,{status:upstream.status});
 if(upstream.ok&&path.join("/")==="auth/login"&&data.access_token){const success=NextResponse.json({success:true});success.cookies.set("fuuud_session",data.access_token,{httpOnly:true,sameSite:"lax",secure:process.env.NODE_ENV==="production",maxAge:data.expires_in,path:"/"});return success}
 return response}
export const GET=proxy;export const POST=proxy;export const PATCH=proxy;
