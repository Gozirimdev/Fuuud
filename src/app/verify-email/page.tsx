import {EmailVerification} from "@/components/email-verification";
export default async function VerifyEmailPage({searchParams}:{searchParams:Promise<{token?:string;email?:string}>}){const {token="",email=""}=await searchParams;return <EmailVerification token={token} email={email}/>}
