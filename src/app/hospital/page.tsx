import {WorkspaceOverview} from "@/components/workspace-overview";
import {requireUserRole} from "@/lib/auth";
export default async function HospitalDashboard(){const user=await requireUserRole("hospital_staff");return <WorkspaceOverview user={user} kind="hospital"/>}
