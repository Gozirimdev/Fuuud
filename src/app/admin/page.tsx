import {WorkspaceOverview} from "@/components/workspace-overview";
import {requireUserRole} from "@/lib/auth";
export default async function AdminDashboard(){const user=await requireUserRole("admin");return <WorkspaceOverview user={user} kind="admin"/>}
