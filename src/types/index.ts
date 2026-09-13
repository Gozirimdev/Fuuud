export type Doctor={id:string;name:string;initials:string;specialty:string;title:string;location:string;experience:number;rating:number;fee:number;next:string;verified:boolean;bio:string};
export type Hospital={id:string;name:string;location:string;distance:string;eta:string;type:string;verified:boolean;emergency:boolean;open:boolean;services:string[]};
export type Prescription={id:string;doctor:string;date:string;status:"Active"|"Previous";medicines:{name:string;dose:string;frequency:string;duration:string}[]};
