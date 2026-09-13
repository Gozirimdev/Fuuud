import {AssistantChat} from "@/components/assistant-chat";
export default async function Agent({searchParams}:{searchParams:Promise<{intent?:string}>}) {
  const {intent} = await searchParams;
  return <AssistantChat key={intent||"new"} intent={intent}/>;
}
