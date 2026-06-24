"use client"

import { TriageResponse, TriageZone } from "@/types/api"
import { formatEUR, ZONE_CONFIG, ZoneKey } from "@/lib/formatters"
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card"
import { Badge } from "@/components/ui/badge"
import { Button } from "@/components/ui/button"
import { Loader2, CheckCircle2, XCircle } from "lucide-react"

// TriageZone is the canonical type for zone.final_zone values
type _TriageZoneRef = TriageZone

interface TriageResultProps {
  result: TriageResponse
  onSharpen: () => void
  isSharpenLoading: boolean
}

export function TriageResult({ result, onSharpen, isSharpenLoading }: TriageResultProps) {
  const zone = result.zone
  const zoneConfig = zone ? ZONE_CONFIG[zone.final_zone as ZoneKey] : null

  return (
    <div className="space-y-4">
      {/* 1. Zone-Badge */}
      {zone !== null && (
        <div className="flex flex-col gap-1">
          <span
            className={`inline-flex items-center rounded-full px-4 py-2 text-base font-semibold ${zoneConfig?.badgeClass}`}
          >
            {zoneConfig?.labelDE}
          </span>
          <p className="text-sm text-muted-foreground">{zone.reason}</p>
        </div>
      )}

      {/* 2. Handlungsdruck-Banner */}
      {zone !== null && zone.handlungsdruck_elevated === true && (
        <div className="rounded-md border border-yellow-300 bg-yellow-50 p-3 text-sm font-medium text-yellow-900">
          Handlungsdruck erkannt — dieser Use Case wurde in eine hoehere Zone hochgestuft.
        </div>
      )}

      {/* 3. Vorfilter-Status */}
      {result.passed_vorfilter === true ? (
        <div className="flex items-center gap-2 rounded-md border border-green-300 bg-green-50 p-3 text-sm font-medium text-green-900">
          <CheckCircle2 className="h-4 w-4 shrink-0" />
          <span>Vorfilter bestanden</span>
        </div>
      ) : (
        <div className="rounded-md border border-red-300 bg-red-50 p-3 text-sm">
          <div className="flex items-center gap-2 font-medium text-red-900">
            <XCircle className="h-4 w-4 shrink-0" />
            <span>Vorfilter nicht bestanden</span>
          </div>
          {result.vorfilter.failed_criteria.length > 0 && (
            <ul className="mt-2 list-disc pl-6 text-red-800">
              {result.vorfilter.failed_criteria.map((criterion, i) => (
                <li key={i}>{criterion}</li>
              ))}
            </ul>
          )}
        </div>
      )}

      {/* 4. ROI-Karten */}
      {result.roi !== null && (
        <div className="grid grid-cols-1 gap-4 sm:grid-cols-3">
          <Card>
            <CardHeader>
              <CardTitle>Erwarteter Nettonutzen</CardTitle>
            </CardHeader>
            <CardContent>
              <p className="text-2xl font-bold">
                {formatEUR(result.roi.net_expected_benefit_eur)}
              </p>
            </CardContent>
          </Card>
          <Card>
            <CardHeader>
              <CardTitle>Theoretisches Potenzial</CardTitle>
            </CardHeader>
            <CardContent>
              <p className="text-2xl font-bold">
                {formatEUR(result.roi.theoretical_potential_eur)}
              </p>
            </CardContent>
          </Card>
          <Card>
            <CardHeader>
              <CardTitle>Stunden/Jahr</CardTitle>
            </CardHeader>
            <CardContent>
              <p className="text-2xl font-bold">
                {result.roi.hours_per_year.toLocaleString("de-DE", {
                  maximumFractionDigits: 0,
                })}
              </p>
            </CardContent>
          </Card>
        </div>
      )}

      {/* 5. Routing-Empfehlung */}
      <Card>
        <CardHeader>
          <CardTitle>Routing-Empfehlung</CardTitle>
        </CardHeader>
        <CardContent className="space-y-2">
          <div className="flex items-center gap-2">
            <span className="text-sm font-medium text-muted-foreground">Empfehlung:</span>
            <Badge variant="outline">{result.routing.recommendation}</Badge>
          </div>
          <div>
            <span className="text-sm font-medium text-muted-foreground">Konfidenz: </span>
            <span className="text-sm">{result.routing.confidence}</span>
          </div>
          {result.routing.risk_flags.length > 0 && (
            <div className="flex flex-wrap gap-1">
              {result.routing.risk_flags.map((flag, i) => (
                <Badge key={i} className="border-red-200 bg-red-100 text-red-800">
                  {flag}
                </Badge>
              ))}
            </div>
          )}
          {result.routing.requires_human_review === true && (
            <p className="text-sm font-medium text-orange-700">
              Menschliche Pruefung empfohlen
            </p>
          )}
        </CardContent>
      </Card>

      {/* 6. Machbarkeit */}
      <Card>
        <CardHeader>
          <CardTitle>Machbarkeit</CardTitle>
        </CardHeader>
        <CardContent className="space-y-2">
          <div className="flex items-center gap-2">
            {result.feasibility.is_feasible ? (
              <CheckCircle2 className="h-4 w-4 text-green-600" />
            ) : (
              <XCircle className="h-4 w-4 text-red-600" />
            )}
            <span className="text-sm font-medium">
              {result.feasibility.is_feasible ? "Machbar" : "Nicht machbar"}
            </span>
          </div>
          {result.feasibility.recommendation !== null && (
            <p className="text-sm">{result.feasibility.recommendation}</p>
          )}
          {result.feasibility.flags.length > 0 && (
            <div className="flex flex-wrap gap-1">
              {result.feasibility.flags.map((flag, i) => (
                <Badge key={i} variant="outline">
                  {flag}
                </Badge>
              ))}
            </div>
          )}
        </CardContent>
      </Card>

      {/* 7. Schaerfen-Button */}
      <div>
        <Button onClick={onSharpen} disabled={isSharpenLoading} className="w-full">
          {isSharpenLoading && <Loader2 className="mr-2 h-4 w-4 animate-spin" />}
          {isSharpenLoading ? "Wird geschaerft..." : "Use Case schaerfen (KI)"}
        </Button>
        <p className="mt-2 text-center text-xs text-muted-foreground">
          Dauert 5-30 Sekunden, LLM-Call
        </p>
      </div>
    </div>
  )
}

export default TriageResult
