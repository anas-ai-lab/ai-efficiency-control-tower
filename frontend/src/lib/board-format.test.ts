import { describe, expect, test } from "vitest";

import {
  computeAxisTicks,
  computeNiceDomainMax,
  formatAxisTickValue,
} from "./board-format";

describe("computeNiceDomainMax", () => {
  test("waehlt die naechste Nice-Stufe ueber dem 1,15-fachen Hoechstwert", () => {
    // 40.000 x 1,15 = 46.000 -> naechste Stufe der {1,2,2.5,5,10}-Folge
    expect(computeNiceDomainMax(40_000)).toBe(50_000);
  });

  test("bleibt auf der Stufe, wenn der Puffer sie gerade noch nicht sprengt", () => {
    // 43.478 x 1,15 = 49.999,7 -> 50.000 reicht noch
    expect(computeNiceDomainMax(43_478)).toBe(50_000);
  });

  test("springt auf die naechste Stufe, sobald der Puffer sie ueberschreitet", () => {
    // 43.480 x 1,15 = 50.002 -> 50.000 reicht nicht mehr, naechste ist 100.000
    expect(computeNiceDomainMax(43_480)).toBe(100_000);
  });

  test("nutzt die 2,5er-Stufe innerhalb einer Zehnerpotenz", () => {
    // 200.000 x 1,15 = 230.000 -> 250.000 (nicht 500.000)
    expect(computeNiceDomainMax(200_000)).toBe(250_000);
  });

  test("skaliert im Zehntausender-Bereich", () => {
    expect(computeNiceDomainMax(18_400)).toBe(25_000);
  });

  test("skaliert im Millionen-Bereich", () => {
    // 1.500.000 x 1,15 = 1.725.000 -> 2 Mio.
    expect(computeNiceDomainMax(1_500_000)).toBe(2_000_000);
  });

  test("faellt bei Hoechstwert 0 auf den Default zurueck", () => {
    expect(computeNiceDomainMax(0)).toBe(100_000);
  });

  test("faellt bei rein negativem Portfolio auf den Default zurueck", () => {
    expect(computeNiceDomainMax(-25_000)).toBe(100_000);
  });
});

describe("computeAxisTicks", () => {
  test("teilt eine 2er-Stufe in vier Schritte", () => {
    expect(computeAxisTicks(200_000)).toEqual([
      0, 50_000, 100_000, 150_000, 200_000,
    ]);
  });

  test("teilt eine 1er-Stufe in fuenf Schritte", () => {
    expect(computeAxisTicks(100_000)).toEqual([
      0, 20_000, 40_000, 60_000, 80_000, 100_000,
    ]);
  });

  test("teilt eine 2,5er-Stufe in fuenf Schritte", () => {
    expect(computeAxisTicks(250_000)).toEqual([
      0, 50_000, 100_000, 150_000, 200_000, 250_000,
    ]);
  });

  test("liefert im Millionen-Bereich runde Schritte", () => {
    expect(computeAxisTicks(2_000_000)).toEqual([
      0, 500_000, 1_000_000, 1_500_000, 2_000_000,
    ]);
  });

  test("bleibt im geforderten 4-6-Tick-Korridor", () => {
    for (const max of [25_000, 50_000, 100_000, 200_000, 250_000, 500_000]) {
      const ticks = computeAxisTicks(max);
      expect(ticks.length).toBeGreaterThanOrEqual(4);
      expect(ticks.length).toBeLessThanOrEqual(6);
      expect(ticks[0]).toBe(0);
      expect(ticks[ticks.length - 1]).toBe(max);
    }
  });

  test("respektiert eine explizit gewuenschte Tick-Anzahl", () => {
    expect(computeAxisTicks(200_000, 3)).toEqual([0, 100_000, 200_000]);
  });

  test("liefert bei Domain-Max 0 nur den Nullpunkt", () => {
    expect(computeAxisTicks(0)).toEqual([0]);
  });
});

describe("formatAxisTickValue", () => {
  test("formatiert 0 ohne Nachkommastellen", () => {
    expect(formatAxisTickValue(0, "de")).toBe("0");
    expect(formatAxisTickValue(0, "en")).toBe("0");
  });

  test("rechnet in Millionen um (de)", () => {
    expect(formatAxisTickValue(500_000, "de")).toBe("0,5");
    expect(formatAxisTickValue(1_500_000, "de")).toBe("1,5");
    expect(formatAxisTickValue(3_000_000, "de")).toBe("3");
  });

  test("rechnet in Millionen um (en)", () => {
    expect(formatAxisTickValue(500_000, "en")).toBe("0.5");
    expect(formatAxisTickValue(1_500_000, "en")).toBe("1.5");
    expect(formatAxisTickValue(3_000_000, "en")).toBe("3");
  });
});
