// Harter Reload der aktuellen Seite statt router.refresh().
//
// Auf der Case-Detailseite greift router.refresh() im Prod-Build NICHT durch:
// der Client-Router-Cache liefert die alte RSC-Nutzlast weiter, sodass eine
// gerade persistierte Admin-Aktion (Schaerfen-Uebernehmen, Loesung, Compliance,
// Entscheidung) in der UI nicht erscheint -- obwohl der SSR-/RSC-Endpoint frisch
// ist (no-store, force-dynamic). Ein window.location.reload() zieht den frischen
// SSR-Stand zuverlaessig. Zentral, damit alle Detail-Aktionen dasselbe Muster
// nutzen (siehe fix 86791c3).
export function hardRefresh(): void {
  window.location.reload();
}
