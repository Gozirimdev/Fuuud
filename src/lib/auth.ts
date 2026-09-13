import {cookies} from "next/headers";
import {redirect} from "next/navigation";

import {getCurrentUser} from "@/lib/api";
import type {ApiUser, UserRole} from "@/lib/api/types";

export async function requireUserRole(role: UserRole): Promise<ApiUser> {
  const token = (await cookies()).get("fuuud_session")?.value;
  if (!token) redirect(`/login?next=${encodeURIComponent(`/${role === "hospital_staff" ? "hospital" : role}`)}`);
  let user: ApiUser;
  try {
    user = await getCurrentUser(token);
  } catch {
    redirect("/login");
  }
  if (user.role !== role) redirect(user.role === "patient" ? "/" : user.role === "hospital_staff" ? "/hospital" : `/${user.role}`);
  return user;
}
