# AI Prompt Template — LLD készítés HLD alapján

---

## Context:
> *(Milyen projektről van szó, melyik fázisban tartunk, ki a megrendelő,
> mikor kell szállítani az LLD-t, ki fogja implementálni a tervet)*

```
Projekt neve          : SOTE LLD
Megrendelő / ügyfél  : Semelweis...............................................
Projekt fázis         : LLD generálás..............................................
LLD határidő          : 2026.09.01...............................................
Implementációt végzi  : Uzsoki Márk...............................................
Egyéb háttér          : ...............................................
```

---

## Role:
> *(Milyen szakértői szerepet vegyen fel az AI: pl. Senior Network Engineer,
> Implementation Engineer, Cisco CCNP/CCIE szintű tervező,
> aki implementáció-kész részletességgel dolgozik)*

```
Network Design Expert...............................................................
```

---

## HLD Input:
> *(Illeszd be ide a HLD dokumentum tartalmát vagy a legfontosabb részeit:
> topológia leírás, tervezési döntések, eszközlista, IP tartományok, VLAN koncepció,
> routing döntések, biztonsági zónák, redundancia stratégia)*

```
SOTE-Halozatfejlesztes-HLD-V11.docx a könyvtárban...............................................................
...............................................................
...............................................................
...............................................................
```

---

## Scope — Mit kell LLD-ben kidolgozni:
> *(Jelöld be melyik területekre kell részletes LLD — töröld ami nem releváns)*

```
[ x] IP Addressing Plan       — minden interface, loopback, management IP
[ x] VLAN Design              — VLAN ID, név, subnet, VTP/trunk mátrix
[ x] Routing Protocol         — OSPF/BGP/EIGRP: area, process-id, timer, redistrib.
[x ] Switching Design         — STP mode, root bridge, portfast, BPDU guard
[x ] Physical Connectivity    — port mátrix, kábeltípus, patch panel terv
[ x] WAN / Uplink             — interfész paraméterek, QoS policy, failover logika
[ x] Security Policies        — ACL, zóna-párok, tűzfal szabálylista
[ x] High Availability        — HSRP/VRRP/GLBP: VIP, priority, preempt, timers
[ x] Management Plane         — OOB, SNMP, Syslog, NTP, AAA, SSH policy
[x ] Wireless                 — AP—switch port mapping, SSID—VLAN binding, QoS
[x ] Data Center Fabric       — VNI, L2/L3 VNI, BGP EVPN konfig
[x ] Configuration Templates  — eszközönkénti CLI konfig blokkok
[ x] Change / Migration Plan  — lépések sorrendje, rollback pont, maintenace window
```

---

## Device Inventory:
> *(Eszközök listája amire konfigurációt / tervet kell készíteni)*

megtalálod a hld-ben. Több variáns is lesz

---

## IP Address Ranges:
> *(HLD-ben meghatározott IP tartományok — LLD ezekből osztja ki a konkrét címeket)*

```
Rendeltetés               | Hálózat / Prefix       | Megjegyzés
--------------------------|------------------------|--------------------
Management                | ...                    | ...
LAN / User VLAN-ok        | ...                    | ...
Server / DMZ              | ...                    | ...
WAN / Uplink              | ...                    | ...
Loopback / Router-ID      | ...                    | ...
Egyéb                     | ...                    | ...
```

---

## Naming Conventions:
> *(Elnevezési szabályok — ezeket kövesse az AI a konfig generálásakor)*

```
Hostname pattern    : Adj példákat..............................................
Interface leírás    : Adj példákat...............................................
VLAN név pattern    : Adj példákat..............................................
ACL / policy név    : Adj példákat...............................................
Loopback logika     : Adj példákat...............................................
```

---

## Output:
> *(Mit várasz el az LLD végeredményeként)*

```
[x ] Teljes IP cím táblázat (minden eszköz, minden interface)
[x ] VLAN táblázat (ID, név, subnet, tagged portok)
[x ] Port mátrix (melyik eszköz melyik portja hova megy)
[x ] Routing konfiguráció részletei (neighbor, area, network statement)
[x ] HA paraméterek (VIP, priority, timer értékek)
[x ] Eszközönkénti CLI konfigurációs blokkok
[ x] Migrációs / implementációs lépések sorrendben
[x ] Rollback terv
[ ] Egyéb: ...............................................
```

---

## Format:
> *(Milyen formában kapd meg az LLD-t)*

```
[x ] Markdown táblázatok + konfigblokkok
[x ] Cisco IOS / IOS-XE CLI konfig (copy-paste kész)
[x ] Cisco NX-OS CLI konfig
[x ] ASCII topológia diagram
[xx ] Mermaid diagram
[x ] Sima bullet point lista
[ x] Egyéb: ...............................................
```

---

## Goal:
> *(Mi a konkrét cél ezzel az LLD-vel: pl. implementációs alap, tender dokumentáció,
> change request alap, átadás-átvétel dokumentum, belső tudástár)*

teljes LLD gyártása

## Example #1:
> *(HLD részlet + milyen LLD részletet vársz belőle)*

**HLD részlet:**
```
...............................................................
```

**Elvárt LLD tartalom / stílus:**
```
magas minőség...............................................................
```

---

## Example #2:
> *(Másik HLD elem — pl. routing vagy HA rész — és a hozzá tartozó LLD mélység)*

**HLD részlet:**
```
...............................................................
```

**Elvárt LLD tartalom / stílus:**
```
...............................................................
```

---

## ASK:
> Kérdezz legalább **3 tisztázó kérdést** és fogalmazz meg **3 feltételezést** a fenti template alapján,
> mielőtt elkezded az LLD összeállítását.
> Haladj fejezetenként, és **csak akkor lépj tovább a következő fejezetre,
> ha az aktuálisat jóváhagytam.**

```
Az AI által felteendő 3 tisztázó kérdés és 3 feltételezés helye —
ezt az AI tölti ki a template alapján, nem te.
```

---

*Template verzió: 1.0 | Cél: LLD generálás HLD dokumentumból*
