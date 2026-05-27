# AI Prompt Template — Network Design

---

## Context:
> *(Írj ide háttérinformációt: milyen szervezetről / projektről van szó, mekkora a méret,
> milyen iparág, van-e meglévő hálózat amit fejleszteni kell, vagy greenfield tervezés,
> mik a meghajtó tényezők: növekedés, compliance, teljesítmény, költség)*

```
...............................................................
...............................................................
...............................................................
```

---

## Role:
> *(Milyen szakértői szerepet vegyen fel az AI: pl. Senior Network Architect, Cisco CCIE Design,
> SD-WAN Solution Architect, Data Center Network Designer stb.)*

```
...............................................................
```

---

## Requirements:
> *(Funkcionális és nem-funkcionális követelmények: felhasználók száma, helyszínek, sávszélesség igény,
> rendelkezésre állási SLA, biztonsági elvárások, compliance pl. ISO 27001 / PCI-DSS,
> IPv4/IPv6, wireless igény, WAN kapcsolat típusa)*

```
Helyszínek száma      : ...............................................
Felhasználók száma    : ...............................................
Sávszélesség igény    : ...............................................
Rendelkezésre állás   : ...............................................
Biztonsági elvárások  : ...............................................
Compliance            : ...............................................
Egyéb követelmények   : ...............................................
```

---

## Constraints:
> *(Korlátok és kötöttségek: budget, meglévő eszközök amiket meg kell tartani, vendor lock-in,
> időkeret, csapatlétszám / szaktudás, tiltott technológiák)*

```
Budget                : ...............................................
Meglévő infrastruktúra: ...............................................
Vendor preferencia    : ...............................................
Határidő              : ...............................................
Tiltott technológiák  : ...............................................
```

---

## Input:
> *(Milyen adatokat adsz meg a tervezéshez: meglévő topológia diagram, IP-cím tartomány,
> VLAN séma, forgalmi mátrix, szerződéses feltételek, tender dokumentáció)*

```
...............................................................
...............................................................
...............................................................
```

---

## Output:
> *(Mit várasz el végeredményként: pl. High-Level Design dokumentum, Low-Level Design,
> IP addressing terv, VLAN séma, eszközlista BOM-mal, konfigurációs template-ek,
> kockázatelemzés, migrációs terv)*

```
...............................................................
...............................................................
```

---

## Format:
> *(Milyen formában kapd meg a választ: pl. markdown fejezetek, táblázatok, ASCII topológia diagram,
> Cisco IOS / NX-OS konfigblokkok, bullet point lista, mermaid diagram)*

```
...............................................................
...............................................................
```

---

## Goal:
> *(Mi a végső cél: pl. skálázható kampuszháló tervezése, DC fabric kiváltása,
> WAN modernizálás SD-WAN-ra, Zero Trust hálózati architektúra, egységes multi-site topológia)*

```
...............................................................
...............................................................
```

---

## Design Layers:
> *(Jelöld be melyik réteg(ek)re van szükség tervhez — töröld ami nem releváns)*

```
[ ] Physical layer      — eszközök, kábelezés, rack elhelyezés
[ ] Network layer       — IP séma, routing protokoll, VLAN design
[ ] Security layer      — zónák, tűzfal politika, szegmentálás, NAC
[ ] WAN / SD-WAN layer  — uplink, failover, QoS, MPLS / internet
[ ] Wireless layer      — AP elhelyezés, SSID séma, roaming
[ ] Data Center layer   — fabric, overlay (VXLAN/EVPN), compute
[ ] Management layer    — out-of-band, monitoring, automation
[ ] High Availability   — redundancia, failover idő, FHRP
```

---

## Example #1:
> *(Adj meg egy konkrét mintapéldát: tervezési feladat röviden + elvárt AI válasz stílusa)*

**Feladat:**
```
...............................................................
```

**Elvárt válasz stílus / tartalom:**
```
...............................................................
```

---

## Example #2:
> *(Második mintapélda — más helyszín méret, technológia vagy tervezési fázis)*

**Feladat:**
```
...............................................................
```

**Elvárt válasz stílus / tartalom:**
```
...............................................................
```

---

## ASK:
> Kérdezz legalább **3 tisztázó kérdést** és fogalmazz meg **3 feltételezést** a fenti template alapján,
> mielőtt elkezded a tervezést.
> Haladj lépésről lépésre, és **csak akkor indítsd a tényleges design munkát, ha mindenben megállapodtunk.**

```
Az AI által felteendő 3 tisztázó kérdés és 3 feltételezés helye —
ezt az AI tölti ki a template alapján, nem te.
```

---

*Template verzió: 1.0 | Cél: Network Design AI Prompt*
