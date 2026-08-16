// Gemeinsamer Attributname fuer Server- und Client-Komponenten. Bewusst
// ausserhalb von leaf-transition.tsx: Dessen "use client"-Grenze wuerde den
// Export im Server-Bundle durch einen Client-Stub ersetzen.
export const LEAF_ORIGIN_ATTR = "data-leaf-origin"
