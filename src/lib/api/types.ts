export type UserRole="patient"|"doctor"|"hospital_staff"|"admin";
export type AccountStatus="pending"|"active"|"suspended";
export type ApiUser={id:string;first_name:string;last_name:string;email:string;role:UserRole;account_status:AccountStatus;phone_number:string|null;country:string|null;state:string|null;city:string|null;email_verified:boolean};
export type ApiDoctor={id:string;first_name:string;last_name:string;specialty:string;professional_title:string;country:string;state:string;city:string;consultation_fee:string;years_of_experience:number;verification_status:"pending"|"verified"|"rejected";bio:string;rating:string;profile_image_url:string|null};
export type ApiAvailability={id:string;practitioner_id:string;date:string;start_time:string;end_time:string;status:"available"|"booked"|"unavailable"};
export type ApiAppointment={id:string;practitioner_id:string;availability_id:string;appointment_type:"online"|"physical";status:"pending"|"confirmed"|"completed"|"cancelled";scheduled_at:string;reason:string;notes:string|null;practitioner:ApiDoctor};
export type ApiAuditEvent={id:string;event_type:string;created_at:string};
export type DoctorQuery={search?:string;specialty?:string;city?:string;max_fee?:string;verified_only?:boolean;available_date?:string;sort?:string;page?:number};
