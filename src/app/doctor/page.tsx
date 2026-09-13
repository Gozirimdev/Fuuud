import {WorkspaceOverview} from "@/components/workspace-overview";
import {requireUserRole} from "@/lib/auth";
export default async function DoctorDashboard(){const user=await requireUserRole("doctor");return <WorkspaceOverview user={user} kind="doctor"/>}
