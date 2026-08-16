"use client";

import { createContext, useContext, useState } from "react";

import {
  Tabs,
  TabsContent,
  TabsList,
  TabsTrigger,
} from "@/components/ui/tabs";

// Case-Detailseite als Reiter statt endlosem Scroll (Ticket-Punkt 5.3a).
// Bekommt die drei Bereiche als FERTIG GERENDERTE Server-Komponenten-Ausgabe
// (page.tsx traegt weiterhin die gesamte Daten-/Auth-Logik) -- diese
// Komponente ist reine Praesentations-/Zustandslogik, kein Datenzugriff.

type TabValue = "use-case" | "analysis" | "decision";

// Vom "Freigabe gesperrt"-Hinweis genutzt, um auf den Use-Case-Reiter zu
// springen (Ersatz fuer den frueheren Anchor-Link "#use-case", der mit Tabs
// nicht mehr funktioniert -- server-gerenderter Inhalt kann keinen
// Client-State direkt setzen, daher der Umweg ueber Context).
const TabSwitchContext = createContext<((tab: TabValue) => void) | null>(null);

export function JumpToUseCaseButton({
  children,
  className,
}: {
  children: React.ReactNode;
  className?: string;
}) {
  const switchTab = useContext(TabSwitchContext);
  if (switchTab === null) return null;
  return (
    <button
      type="button"
      onClick={() => switchTab("use-case")}
      className={className}
    >
      {children}
    </button>
  );
}

export function CaseDetailTabs({
  useCaseTitle,
  useCaseContent,
  analysisTitle,
  analysisContent,
  decisionTitle,
  decisionContent,
}: {
  useCaseTitle: string;
  useCaseContent: React.ReactNode;
  analysisTitle: string | null;
  analysisContent: React.ReactNode | null;
  decisionTitle: string;
  decisionContent: React.ReactNode;
}) {
  const [tab, setTab] = useState<TabValue>("use-case");
  const hasAnalysis = analysisContent !== null && analysisTitle !== null;

  return (
    <TabSwitchContext.Provider value={setTab}>
      <Tabs
        value={tab}
        onValueChange={(v) => setTab(v as TabValue)}
        className="mt-8 w-full"
      >
        <TabsList className="h-auto min-h-8 w-full items-stretch">
          <TabsTrigger
            value="use-case"
            className="h-auto min-w-0 flex-1 whitespace-normal py-1.5 leading-tight"
          >
            {useCaseTitle}
          </TabsTrigger>
          {hasAnalysis && (
            <TabsTrigger
              value="analysis"
              className="h-auto min-w-0 flex-1 whitespace-normal py-1.5 leading-tight"
            >
              {analysisTitle}
            </TabsTrigger>
          )}
          <TabsTrigger
            value="decision"
            className="h-auto min-w-0 flex-1 whitespace-normal py-1.5 leading-tight"
          >
            {decisionTitle}
          </TabsTrigger>
        </TabsList>
        <TabsContent value="use-case" className="pt-6">
          {useCaseContent}
        </TabsContent>
        {hasAnalysis && (
          <TabsContent value="analysis" className="pt-6">
            {analysisContent}
          </TabsContent>
        )}
        <TabsContent value="decision" className="pt-6">
          {decisionContent}
        </TabsContent>
      </Tabs>
    </TabSwitchContext.Provider>
  );
}
