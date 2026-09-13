import type {Metadata} from "next";
import "./globals.css";
import "./auth-layout.css";
import "./home-motion.css";
import {Shell} from "@/components/layout";
export const metadata:Metadata={title:{default:"Fuuud — Care, closer.",template:"%s · Fuuud"},description:"Find a doctor, plan your next visit, and find a clearer path to care with Fuuud."};
export default function RootLayout({children}:{children:React.ReactNode}){return <html lang="en"><body><Shell>{children}</Shell></body></html>}
