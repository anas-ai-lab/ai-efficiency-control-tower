import type { Metadata } from "next";
import { getTranslations } from "next-intl/server";

import { IdeationView } from "@/components/ideation-view";

export async function generateMetadata(): Promise<Metadata> {
  const t = await getTranslations("ideation");
  return { title: t("metaTitle") };
}

export default function IdeationPage() {
  return <IdeationView />;
}
