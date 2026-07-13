import type { Metadata } from "next";
import { getTranslations } from "next-intl/server";

import { LoginForm } from "@/components/login-form";

export async function generateMetadata(): Promise<Metadata> {
  const t = await getTranslations("login");
  return { title: t("metaTitle") };
}

export default async function LoginPage({
  searchParams,
}: {
  searchParams: Promise<{ next?: string }>;
}) {
  // ?next= tragen die Admin-Routen bei (Ruecksprung nach dem Login).
  const { next } = await searchParams;
  const t = await getTranslations("login");

  return (
    <main className="mx-auto max-w-md px-5 py-16 sm:px-6">
      <p className="eyebrow">{t("eyebrow")}</p>
      <h1 className="mt-3 text-2xl font-semibold tracking-tight text-foreground">
        {t("title")}
      </h1>
      <p className="mt-2 mb-8 max-w-prose text-sm leading-relaxed text-muted-foreground">
        {t("intro")}
      </p>
      <LoginForm next={next} />
    </main>
  );
}
