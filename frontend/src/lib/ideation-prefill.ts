// P14-Handoff (D16/D17): Der Ideen-Assistent (/ideation) legt einen
// uebernommenen Entwurf unter diesem sessionStorage-Key ab; das Intake-Formular
// liest ihn beim Mount einmalig aus und loescht ihn sofort (read-once). Nur die
// qualitativen Felder werden uebergeben -- der Payload traegt exakt die
// UseCaseInput-Feldnamen, damit das Formular sie ohne Umbenennung als
// Startwerte setzen kann. Quantitative Felder werden NIE uebergeben (doppelter
// Boden zu D17: der Assistent erfindet keine Zahlen, das Formular befuellt sie
// nicht vor).
export const IDEATION_PREFILL_KEY = "aect_ideation_prefill";

// Payload-Form des Handoffs. Bewusst nur die vier qualitativen Felder -- die
// Whitelist im Formular verlaesst sich nicht darauf (sie prueft die Feldnamen
// erneut), aber der Erzeuger schreibt nichts anderes hinein.
export interface IdeationPrefill {
  title: string;
  current_state: string;
  desired_state: string;
  example_process: string;
}
