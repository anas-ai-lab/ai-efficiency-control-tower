"use client"

import Link from "next/link"
import { ArrowRight } from "lucide-react"
import {
  motion,
  useMotionValue,
  useReducedMotion,
  useSpring,
  type Variants,
} from "motion/react"

import { LEAF_ORIGIN_ATTR } from "@/components/leaf-transition"

// Navigations-Kachel der Startseite (v4.2).
//
// HOVER -- ausdruecklich KEIN reines Scale (eine vergroesserte Karte ist die
// billigste Form von Feedback und laesst Text neu rastern). Stattdessen drei
// zusammenspielende Signale, alle federbasiert:
//   1. Elevation: die Kachel hebt 3px und bekommt einen weicheren Schatten.
//   2. Akzent-Hairline: eine Linie laeuft von links unter der Kachel ein.
//   3. Icon-Mikro-Bewegung: Icon hebt minimal, der Pfeil rueckt nach rechts.
// Touch hat keinen Hover -- daher whileTap als gleichwertiger Pressed-State
// (Kachel senkt sich statt zu heben, Hairline laeuft trotzdem ein).
// Tastatur ist gleichwertig ueber whileFocus + sichtbarem Ring.
const MotionLink = motion.create(Link)

// Eine Feder fuer alle drei Signale -- ein Bewegungsgefuehl, nicht drei.
const SPRING = { type: "spring" as const, stiffness: 380, damping: 32, mass: 0.6 }

const tileVariants: Variants = {
  rest: { y: 0, boxShadow: "0 1px 2px 0 rgb(0 0 0 / 0.04)" },
  active: { y: -3, boxShadow: "0 12px 28px -12px rgb(0 0 0 / 0.18)" },
  press: { y: -1, boxShadow: "0 4px 12px -6px rgb(0 0 0 / 0.14)" },
}

const hairlineVariants: Variants = {
  rest: { scaleX: 0, opacity: 0 },
  active: { scaleX: 1, opacity: 1 },
  press: { scaleX: 1, opacity: 1 },
}

const iconVariants: Variants = {
  rest: { y: 0 },
  active: { y: -2 },
  press: { y: 0 },
}

const arrowVariants: Variants = {
  rest: { x: 0, opacity: 0.55 },
  active: { x: 3, opacity: 1 },
  press: { x: 1, opacity: 1 },
}

// CURSOR-TILT + SPOTLIGHT (v4.3) -- ADDITIV zu den vier Signalen oben, die
// unveraendert weiterlaufen. Beides haengt an einer echten Cursor-Position und
// ist damit bewusst NUR fuer die Maus: bei Tastatur-Fokus gibt es keinen Punkt,
// dem der Spotlight folgen koennte, und ein Kippen ohne Ursache waere Unruhe.
// Die Tastatur ist ueber whileFocus (Elevation + Hairline + Icon) und den
// Fokusring bereits gleichwertig bedient -- hier fehlt nichts.
// Eigene, weichere Feder als SPRING: die Kippung soll dem Cursor nachlaufen,
// nicht auf ihm sitzen.
const TILT_SPRING = {
  type: "spring" as const,
  stiffness: 300,
  damping: 24,
  mass: 0.5,
}

export interface NavTileProps {
  href: string
  title: string
  description: string
  // FERTIG GERENDERTES Element, kein Komponenten-Typ: die Kachel wird aus der
  // Server-Komponente landing.tsx heraus befuellt, und ueber die RSC-Grenze
  // laesst sich keine Funktion reichen (Lucide-Icons sind forwardRef-Objekte ->
  // "Functions cannot be passed directly to Client Components", erst zur
  // Laufzeit sichtbar, nicht im Build). React-Elemente sind serialisierbar.
  icon: React.ReactNode
}

export function NavTile({ href, title, description, icon }: NavTileProps) {
  const reduce = useReducedMotion()

  // reduced-motion: keine Transforms, kein Schatten-Sprung. Die Hairline bleibt
  // -- sie blendet dann nur ueber die Deckkraft ein (Opazitaet ist die
  // zugelassene Alternative zu Bewegung), und der Fokusring ist unveraendert.
  const variants: Variants | undefined = reduce
    ? {
        rest: { opacity: 1 },
        active: { opacity: 1 },
        press: { opacity: 1 },
      }
    : tileVariants

  // Rohwerte aus dem Mausereignis, gefedert an das Element gegeben.
  const rawRotateX = useMotionValue(0)
  const rawRotateY = useMotionValue(0)
  const rotateX = useSpring(rawRotateX, TILT_SPRING)
  const rotateY = useSpring(rawRotateY, TILT_SPRING)

  function handleMouseMove(event: React.MouseEvent<HTMLAnchorElement>) {
    if (reduce) return
    const el = event.currentTarget
    const rect = el.getBoundingClientRect()
    const x = event.clientX - rect.left
    const y = event.clientY - rect.top
    // Spotlight folgt ueber CSS-Variablen -- direkt auf dem Element gesetzt,
    // damit die Mausbewegung keinen React-Re-Render pro Frame ausloest.
    el.style.setProperty("--mx", `${(x / rect.width) * 100}%`)
    el.style.setProperty("--my", `${(y / rect.height) * 100}%`)
    // Max. 3,5 Grad. Mehr liest sich als Spielerei und laesst den Text rastern.
    rawRotateX.set(-((y - rect.height / 2) / (rect.height / 2)) * 3.5)
    rawRotateY.set(((x - rect.width / 2) / (rect.width / 2)) * 3.5)
  }

  function handleMouseLeave() {
    rawRotateX.set(0)
    rawRotateY.set(0)
  }

  return (
    <MotionLink
      href={href}
      {...{ [LEAF_ORIGIN_ATTR]: "" }}
      initial="rest"
      animate="rest"
      whileHover="active"
      whileFocus="active"
      whileTap="press"
      variants={variants}
      transition={reduce ? { duration: 0 } : SPRING}
      onMouseMove={handleMouseMove}
      onMouseLeave={handleMouseLeave}
      style={reduce ? undefined : { rotateX, rotateY, transformPerspective: 800 }}
      className="group relative flex flex-col overflow-hidden rounded-2xl border border-[var(--hairline-rule)] bg-card p-6 outline-none focus-visible:ring-2 focus-visible:ring-[var(--brand-accent)] focus-visible:ring-offset-2 focus-visible:ring-offset-background"
    >
      {/* Spotlight. Liegt VOR dem Inhalt im DOM, damit er unter allem liegt;
          pointer-events-none, damit er das Ziel des Links nicht abschirmt.
          Ohne Cursor (Tastatur, Touch) bleibt er per opacity-0 unsichtbar. */}
      <span
        aria-hidden
        className="pointer-events-none absolute inset-0 rounded-2xl opacity-0 transition-opacity duration-300 group-hover:opacity-100"
        style={{
          background:
            "radial-gradient(circle at var(--mx,50%) var(--my,50%), color-mix(in oklch, var(--brand-accent), transparent 88%), transparent 60%)",
        }}
      />

      <motion.span
        aria-hidden
        variants={reduce ? undefined : iconVariants}
        transition={SPRING}
        className="flex size-10 items-center justify-center rounded-xl border border-[var(--hairline)] bg-[var(--ink-subtle)] text-[var(--ink)] transition-colors duration-300 group-hover:border-transparent group-hover:bg-[var(--ink)] group-hover:text-[var(--ink-foreground)]"
      >
        {icon}
      </motion.span>

      <span className="mt-5 flex items-center gap-1.5 text-[0.975rem] font-semibold tracking-tight text-foreground">
        {title}
        <motion.span
          aria-hidden
          variants={arrowVariants}
          transition={SPRING}
          className="inline-flex text-muted-foreground"
        >
          <ArrowRight className="size-3.5" />
        </motion.span>
      </span>

      {/* Nutzenversprechen: ein Satz, was die Person hier gewinnt -- nicht, was
          die Seite technisch tut. */}
      <span className="mt-2 text-sm leading-relaxed text-balance text-muted-foreground">
        {description}
      </span>

      {/* Die einlaufende Akzent-Hairline. origin-left -> sie zieht sich von links
          auf, statt aus der Mitte aufzuploppen. */}
      <motion.span
        aria-hidden
        variants={hairlineVariants}
        transition={reduce ? { duration: 0.15 } : SPRING}
        className="absolute inset-x-0 bottom-0 h-px origin-left bg-[var(--hairline-accent)]"
      />
    </MotionLink>
  )
}

export default NavTile
