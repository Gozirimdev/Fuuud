import {NextResponse} from "next/server";export function POST(){const r=NextResponse.json({success:true});r.cookies.set("fuuud_session","",{httpOnly:true,maxAge:0,path:"/"});return r}
