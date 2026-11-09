import type { Metadata } from 'next';
import './globals.css';
export const metadata: Metadata = {title:'MedForge AI | Research workspace',description:'Explainable heart disease classification and evidence review. Educational demonstration only.'};
export default function Layout({children}:{children:React.ReactNode}) { return <html lang="en"><body>{children}</body></html>; }
