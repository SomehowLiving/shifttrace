// Printable test labels: QR codes for machines, parts, bins and shipments. Print them (or open this page on a phone)
// and scan with any camera from the Scan button, a Zebra device or a wedge scanner. Tapping a label simulates the scan.
import { useEffect, useState } from "react";
import QRCode from "qrcode";
import { Printer, ScanBarcode } from "lucide-react";
import { useFetch } from "../live";
import { Btn, PageHead } from "../ui";
import { emitScan } from "../scan";
import { ScanButton } from "../scanner";
import type { Asset, Part } from "../api";

type Label = { code: string; title: string; sub: string; kind: "Machine" | "Part" | "Bin" | "Shipment" };
type PartLoc = Part & { locations?: { location: string; quantity: number }[] };

function Qr({ text }: { text: string }) {
  const [svg, setSvg] = useState("");
  useEffect(() => { QRCode.toString(text, { type: "svg", margin: 1, errorCorrectionLevel: "M", color: { dark: "#000000", light: "#ffffff" } }).then(setSvg).catch(() => setSvg("")); }, [text]);
  return <div className="w-full aspect-square bg-white rounded-md p-1 [&>svg]:w-full [&>svg]:h-full" dangerouslySetInnerHTML={{ __html: svg }} />;
}

export default function Labels() {
  const { data: assets } = useFetch<Asset[]>("/api/assets", []);
  const { data: parts } = useFetch<PartLoc[]>("/api/inventory", []);
  const { data: shipments } = useFetch<{ shipment_id: string; status: string; destination?: string; carrier?: string }[]>("/api/shipments", []);

  const bins = new Map<string, string>();
  for (const p of parts ?? []) for (const l of p.locations ?? [{ location: p.location, quantity: p.on_hand }]) if (l.location && !bins.has(l.location)) bins.set(l.location, p.name);
  const groups: [string, Label[]][] = [
    ["Machines", (assets ?? []).map((a) => ({ code: `SHIFTTRACE:${a.asset_id}`, title: a.asset_id, sub: a.name, kind: "Machine" as const }))],
    ["Parts and stock items", (parts ?? []).map((p) => ({ code: p.part_id, title: p.part_id, sub: p.name, kind: "Part" as const }))],
    ["Bins and locations", [...bins.entries()].map(([loc, name]) => ({ code: loc, title: loc, sub: name, kind: "Bin" as const }))],
    ["Shipments", (shipments ?? []).map((s) => ({ code: s.shipment_id, title: s.shipment_id, sub: [s.carrier, s.status].filter(Boolean).join(" · "), kind: "Shipment" as const }))],
  ];

  const tap = (l: Label) => emitScan(l.code);  // same path as a hardware scan: a machine opens; anything else is explained

  return (
    <div className="max-w-[1200px] mx-auto px-4 sm:px-6 py-6 grid gap-6">
      <div className="print:hidden">
        <PageHead title="Test labels" sub="QR labels for the demo machines, parts, bins and shipments. Print them or show them on a phone, then scan with the Scan button (any camera), a Zebra device or a keyboard-wedge scanner. No scanner? Tap a label to simulate the scan."
          right={<div className="flex gap-2"><ScanButton /><Btn onClick={() => window.print()}><Printer size={16} />Print</Btn></div>} />
      </div>
      {groups.map(([name, labels]) => labels.length > 0 && (
        <section key={name} className="grid gap-3 break-inside-avoid">
          <h2 className="text-[15px] font-bold border-t border-rule pt-2">{name} <span className="text-pencil font-normal">({labels.length})</span></h2>
          <div className="grid grid-cols-2 sm:grid-cols-3 md:grid-cols-4 lg:grid-cols-6 gap-3">
            {labels.map((l) => (
              <button key={l.code} onClick={() => tap(l)} data-label={l.code} title={`Simulate scanning ${l.code}`}
                className="group text-left card p-2.5 grid gap-2 hover:border-teal print:border-black print:bg-white print:text-black break-inside-avoid">
                <Qr text={l.code} />
                <div className="min-w-0">
                  <div className="font-mono text-[13px] font-semibold truncate">{l.title}</div>
                  <div className="text-[12px] text-pencil truncate print:text-black">{l.sub}</div>
                </div>
                <span className="print:hidden inline-flex items-center gap-1 text-[11px] text-pencil group-hover:text-teal"><ScanBarcode size={12} />Tap to scan</span>
              </button>
            ))}
          </div>
        </section>
      ))}
      <p className="text-[12px] text-pencil print:text-black">Synthetic demo data. Machine labels encode SHIFTTRACE:&lt;asset id&gt;; the rest encode the plain code.</p>
    </div>
  );
}
