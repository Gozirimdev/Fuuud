import type {ApiAppointment,ApiAuditEvent,ApiAvailability,ApiDoctor,ApiUser,DoctorQuery} from "./types";
const base=process.env.API_URL||process.env.NEXT_PUBLIC_API_URL||"http://localhost:8000";
export class ApiError extends Error{constructor(public status:number,message:string){super(message)}}
async function request<T>(path:string,init?:RequestInit):Promise<T>{const r=await fetch(`${base}/api/v1${path}`,{...init,headers:{"Content-Type":"application/json",...init?.headers},cache:"no-store"});if(!r.ok){const body=await r.json().catch(()=>({}));throw new ApiError(r.status,body.detail||"We couldn't load this information.")}return r.json()}
export async function getDoctors(query:DoctorQuery={}){const params=new URLSearchParams();Object.entries(query).forEach(([k,v])=>{if(v!==undefined&&v!=="")params.set(k,String(v))});return request<{items:ApiDoctor[];total:number;page:number;page_size:number}>(`/doctors?${params}`)}
export const getDoctor=(id:string)=>request<ApiDoctor>(`/doctors/${id}`);
export const getDoctorAvailability=(id:string)=>request<ApiAvailability[]>(`/doctors/${id}/availability`);
export const getCurrentUser=(token:string)=>request<ApiUser>("/users/me",{headers:{Authorization:`Bearer ${token}`}});
export const getMyAppointments=(token:string,view="")=>request<ApiAppointment[]>(`/appointments/me${view?`?view=${view}`:""}`,{headers:{Authorization:`Bearer ${token}`}});
export const getMyAuditEvents=(token:string)=>request<ApiAuditEvent[]>("/users/me/audit-events",{headers:{Authorization:`Bearer ${token}`}});
