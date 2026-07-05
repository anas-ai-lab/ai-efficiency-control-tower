import type { Metadata } from "next";

import { IdeationView } from "@/components/ideation-view";

export const metadata: Metadata = {
  title: "Ideen-Assistent | AECT",
};

export default function IdeationPage() {
  return <IdeationView />;
}
