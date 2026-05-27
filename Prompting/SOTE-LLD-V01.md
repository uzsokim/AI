# Semmelweis Egyetem Hálózatfejlesztés
# Low-Level Design — Variánsfüggetlen rész
## Verzió: 0.1 DRAFT | Dátum: 2026-05-19 | Szerző: Uzsoki Márk

---

> **Hatókör:** Enterprise Core · InterConnect · OOB Zóna · Internet Edge + BGP  
> **Variánsfüggő részek (Disztribúció / Access):** külön LLD fejezet, variáns-döntés után  
> **Forrás HLD:** SOTE-Halozatfejlesztes-HLD-V11.docx

---

## 1. Elnevezési Konvenciók (javaslat)

### 1.1 Hostname séma

```
<CAMPUS>-<SZEREPKÖR>-<SORSZÁM>
```

| Campus prefix | Magyarázat |
|---|---|
| `BKT` | Belgyógyászati és Klinikai Tömb szerverterem |
| `KKT` | Klinikai Komplexum Tömb szerverterem |

| Szerepkör prefix | Eszköztípus |
|---|---|
| `EC` | Enterprise Core (Cisco C9500-48Y4C) |
| `IC` | InterConnect switch |
| `IE` | Internet Edge switch (Cisco C9200L-24P-4X) |
| `OOB-FW` | OOB peremtűzfal |
| `OOB-TSG` | OOB Terminal Server Gateway (C1100TG) |
| `DIST` | Disztribúciós switch (variáns-specifikus) |
| `ACC` | Access switch — épület + emelet kód |

**Példák:**

| Hostname | Eszköz |
|---|---|
| `BKT-EC-1` | BKT Enterprise Core #1 |
| `BKT-EC-2` | BKT Enterprise Core #2 |
| `KKT-EC-1` | KKT Enterprise Core #1 |
| `KKT-EC-2` | KKT Enterprise Core #2 |
| `BKT-IC-1` | BKT InterConnect #1 |
| `BKT-IC-2` | BKT InterConnect #2 |
| `KKT-IC-1` | KKT InterConnect #1 |
| `KKT-IC-2` | KKT InterConnect #2 |
| `BKT-IE-1` | BKT Internet Edge switch |
| `KKT-IE-1` | KKT Internet Edge switch |
| `BKT-OOB-FW` | BKT OOB peremtűzfal |
| `KKT-OOB-FW` | KKT OOB peremtűzfal |
| `BKT-OOB-TSG` | BKT Terminal Server Gateway |
| `KKT-OOB-TSG` | KKT Terminal Server Gateway |

> **Disztribúció (variáns-specifikus):** `<EPULET>-DIST-1` / `<EPULET>-DIST-2`  
> Pl.: `HOGYES-DIST-1`, `BALASSA-DIST-2`, `GYER1-DIST-1`

---

### 1.2 Interface Description séma

```
TO-<CÉLESZKÖZ-HOSTNAME>-<CÉLPORT>   [ <FUNKCIÓ> ]
```

| Példa | Leírás |
|---|---|
| `TO-BKT-IC-1-Te1/0/1 [BACKBONE-40G]` | BKT-EC-1 portján, BKT-IC-1 felé |
| `TO-BKT-OOB-FW-Gi1/0/1 [OOB-MGMT]` | OOB tűzfal felé |
| `TO-PROMC-RTR-BKT-Te1/0/2 [BGP-PRIMARY]` | SP router felé |
| `TO-BKATA-Gi6/1 [KOEGZISZTENCIA-MIGRACIO]` | Legacy core felé (migráció idején) |

---

### 1.3 VLAN névséma

Meglévő VLAN-ok neve **változatlan** marad. Új VLAN-ok:

```
SOTE-<CSOPORT>-<FUNKCIÓ>
```

| VLAN ID | Neve | Funkció |
|---|---|---|
| 2000 | `SOTE-DOLG-CAMPUS` | Általános dolgozók |
| 2001 | `SOTE-MEDI-CAMPUS` | Orvosi/klinikai dolgozók |
| 2002 | `SOTE-TANU-CAMPUS` | Hallgatók |
| 2003 | `SOTE-GAZD-CAMPUS` | Gazdasági dolgozók |
| 2004 | `SOTE-MEDI-TANU-CAMPUS` | Kombinált MEDI+TANU |
| 2005 | `SOTE-MEDI-GAZD-CAMPUS` | Kombinált MEDI+GAZD |
| 2006 | `SOTE-MEDI-GAZD-TANU-CAMPUS` | Hármas kombináció |
| 2007 | `SOTE-GAZD-TANU-CAMPUS` | Kombinált GAZD+TANU |
| 2008 | `SOTE-INFI-CAMPUS` | IT munkatársak |
| 2009 | `SOTE-BIZT-CAMPUS` | Biztonságtechnika |
| 422  | `SOTE-INFADMIN-MGMT` | IT adminisztrátorok |
| 220  | `SOTE-MEDMOB-IOT` | Mobil medikai eszközök |
| 900  | `SOTE-OOB-MGMT` | Out-of-Band management |
| 901  | `SOTE-INFRA-P2P` | Infrastructure P2P linkek |

---

### 1.4 ACL / Prefix-list / Route-map névséma

```
<ESZKÖZ>-<IRÁNY>-<CÉL>-<TÍPUS>
```

| Példa | Leírás |
|---|---|
| `BKT-EC-1-OUT-CAMPUS-PL` | BKT-EC-1-ről kifelé, campus irányba, prefix-list |
| `SOTE-BGP-OUT-PROMC-RM` | BGP kifelé Pro M felé, route-map |
| `SOTE-BGP-IN-PROMC-RM` | BGP befelé Pro M felől, route-map |
| `SOTE-OSPF100-REDIST-RM` | OSPF 100 redistributálási route-map |

---

## 2. IP-Cím Terv (javaslat)

### 2.1 Összefoglaló — meglévő tartományok (érintetlen)

| Tartomány | Szerepkör | Megjegyzés |
|---|---|---|
| `10.63.64.0/21` | Menedzsment (meglévő) | Nexus mgmt VRF default GW: 10.63.64.1 |
| `172.27.0.0/24` | VXLAN underlay loopbackok | Nexus fabric, OSPF Process 2 |
| `172.27.4.0/24` | VXLAN P2P linkek | Nexus fabric underlay |
| `193.6.209.0/24` | BGP / Internet peering | AS 65008, nyilvános |
| `10.10.255.0/30` | OSPF Process 1 (Forti–BKATA) | Megmarad migráció végéig |

---

### 2.2 Új infrastruktúra tartományok

#### 2.2.1 Management — új eszközök

| Tartomány | Eszközök | Prefix |
|---|---|---|
| BKT új infrastruktúra mgmt | BKT-EC-1/2, BKT-IC-1/2, BKT-IE-1, BKT-OOB-FW, BKT-OOB-TSG | `10.63.72.0/24` |
| KKT új infrastruktúra mgmt | KKT-EC-1/2, KKT-IC-1/2, KKT-IE-1, KKT-OOB-FW, KKT-OOB-TSG | `10.63.73.0/24` |
| OOB dedikált hálózat | OOB-FW → OOB-TSG, OOB management interfészek | `10.63.74.0/24` |

**BKT Management IP kiosztás (`10.63.72.0/24`):**

| IP | Hostname | Szerepkör |
|---|---|---|
| `10.63.72.1` | — | Default gateway (Management VLAN SVI) |
| `10.63.72.10` | `BKT-EC-1` | Enterprise Core #1 Management |
| `10.63.72.11` | `BKT-EC-2` | Enterprise Core #2 Management |
| `10.63.72.14` | `BKT-IC-1` | InterConnect #1 Management |
| `10.63.72.15` | `BKT-IC-2` | InterConnect #2 Management |
| `10.63.72.18` | `BKT-IE-1` | Internet Edge switch Management |
| `10.63.72.20` | `BKT-OOB-FW` | OOB tűzfal Management |
| `10.63.72.22` | `BKT-OOB-TSG` | Terminal Server Gateway Management |
| `10.63.72.200–254` | — | DHCP / dinamikus (fenntartott) |

**KKT Management IP kiosztás (`10.63.73.0/24`):**

| IP | Hostname | Szerepkör |
|---|---|---|
| `10.63.73.1` | — | Default gateway (Management VLAN SVI) |
| `10.63.73.10` | `KKT-EC-1` | Enterprise Core #1 Management |
| `10.63.73.11` | `KKT-EC-2` | Enterprise Core #2 Management |
| `10.63.73.14` | `KKT-IC-1` | InterConnect #1 Management |
| `10.63.73.15` | `KKT-IC-2` | InterConnect #2 Management |
| `10.63.73.18` | `KKT-IE-1` | Internet Edge switch Management |
| `10.63.73.20` | `KKT-OOB-FW` | OOB tűzfal Management |
| `10.63.73.22` | `KKT-OOB-TSG` | Terminal Server Gateway Management |

---

#### 2.2.2 Infrastructure Loopbackok (Router-ID-ok)

| IP | Hostname | Szerepkör |
|---|---|---|
| `10.63.75.1/32` | `BKT-EC-1` | OSPF Router-ID / Loopback0 |
| `10.63.75.2/32` | `BKT-EC-2` | OSPF Router-ID / Loopback0 |
| `10.63.75.3/32` | `KKT-EC-1` | OSPF Router-ID / Loopback0 |
| `10.63.75.4/32` | `KKT-EC-2` | OSPF Router-ID / Loopback0 |
| `10.63.75.5/32` | `BKT-IC-1` | OSPF Router-ID / Loopback0 |
| `10.63.75.6/32` | `BKT-IC-2` | OSPF Router-ID / Loopback0 |
| `10.63.75.7/32` | `KKT-IC-1` | OSPF Router-ID / Loopback0 |
| `10.63.75.8/32` | `KKT-IC-2` | OSPF Router-ID / Loopback0 |

---

#### 2.2.3 Infrastructure P2P linkek (OSPF underlay)

Séma: `10.63.76.0/24` — minden link `/30`

| Subnet | A-oldal | B-oldal | Funkció |
|---|---|---|---|
| `10.63.76.0/30` | BKT-EC-1 `.1` | BKT-EC-2 `.2` | EC#1↔EC#2 BKT belső gerinc |
| `10.63.76.4/30` | KKT-EC-1 `.5` | KKT-EC-2 `.6` | EC#1↔EC#2 KKT belső gerinc |
| `10.63.76.8/30` | BKT-EC-1 `.9` | BKT-IC-1 `.10` | EC#1 → IC#1 BKT |
| `10.63.76.12/30` | BKT-EC-1 `.13` | BKT-IC-2 `.14` | EC#1 → IC#2 BKT |
| `10.63.76.16/30` | BKT-EC-2 `.17` | BKT-IC-1 `.18` | EC#2 → IC#1 BKT |
| `10.63.76.20/30` | BKT-EC-2 `.21` | BKT-IC-2 `.22` | EC#2 → IC#2 BKT |
| `10.63.76.24/30` | KKT-EC-1 `.25` | KKT-IC-1 `.26` | EC#1 → IC#1 KKT |
| `10.63.76.28/30` | KKT-EC-1 `.29` | KKT-IC-2 `.30` | EC#1 → IC#2 KKT |
| `10.63.76.32/30` | KKT-EC-2 `.33` | KKT-IC-1 `.34` | EC#2 → IC#1 KKT |
| `10.63.76.36/30` | KKT-EC-2 `.37` | KKT-IC-2 `.38` | EC#2 → IC#2 KKT |
| `10.63.76.40/30` | BKT-IC-1 `.41` | KKT-IC-1 `.42` | IC BKT#1↔KKT#1 cross-site |
| `10.63.76.44/30` | BKT-IC-1 `.45` | KKT-IC-2 `.46` | IC BKT#1↔KKT#2 cross-site |
| `10.63.76.48/30` | BKT-IC-2 `.49` | KKT-IC-1 `.50` | IC BKT#2↔KKT#1 cross-site |
| `10.63.76.52/30` | BKT-IC-2 `.53` | KKT-IC-2 `.54` | IC BKT#2↔KKT#2 cross-site |
| `10.63.76.56/30` | BKT-OOB-FW `.57` | BKT-IC-1 `.58` | OOB-FW BKT → IC#1 |
| `10.63.76.60/30` | BKT-OOB-FW `.61` | BKT-IC-2 `.62` | OOB-FW BKT → IC#2 |
| `10.63.76.64/30` | KKT-OOB-FW `.65` | KKT-IC-1 `.66` | OOB-FW KKT → IC#1 |
| `10.63.76.68/30` | KKT-OOB-FW `.69` | KKT-IC-2 `.70` | OOB-FW KKT → IC#2 |

> **Disztribúció uplink P2P linkek:** külön /24 allokáció a variáns-specifikus LLD-ben.

---

#### 2.2.4 OOB dedikált hálózat

| Subnet | Szerepkör |
|---|---|
| `10.63.74.0/29` | BKT OOB-FW ↔ OOB-TSG management |
| `10.63.74.8/29` | KKT OOB-FW ↔ OOB-TSG management |
| `10.63.74.16/28` | OOB Console hozzáférés admin IP-k (VPN tunnel) |

---

#### 2.2.5 Kliens Campus VLAN-ok (ISE-kiosztott)

> Ezeket az ISE DHCP scope-ként konfigurálja. Az access/disztribúciós réteg SVI-ként terjeszti.

| VLAN ID | Név | Subnet | Hosts | Gateway |
|---|---|---|---|---|
| 2000 | `SOTE-DOLG-CAMPUS` | `10.100.0.0/22` | 1022 | `10.100.0.1` |
| 2001 | `SOTE-MEDI-CAMPUS` | `10.100.4.0/22` | 1022 | `10.100.4.1` |
| 2002 | `SOTE-TANU-CAMPUS` | `10.100.8.0/22` | 1022 | `10.100.8.1` |
| 2003 | `SOTE-GAZD-CAMPUS` | `10.100.12.0/22` | 1022 | `10.100.12.1` |
| 2004 | `SOTE-MEDI-TANU-CAMPUS` | `10.100.16.0/23` | 510 | `10.100.16.1` |
| 2005 | `SOTE-MEDI-GAZD-CAMPUS` | `10.100.18.0/23` | 510 | `10.100.18.1` |
| 2006 | `SOTE-MEDI-GAZD-TANU-CAMPUS` | `10.100.20.0/23` | 510 | `10.100.20.1` |
| 2007 | `SOTE-GAZD-TANU-CAMPUS` | `10.100.22.0/23` | 510 | `10.100.22.1` |
| 2008 | `SOTE-INFI-CAMPUS` | `10.100.24.0/24` | 254 | `10.100.24.1` |
| 2009 | `SOTE-BIZT-CAMPUS` | `10.100.25.0/24` | 254 | `10.100.25.1` |
| 422  | `SOTE-INFADMIN-MGMT` | `10.100.26.0/24` | 254 | `10.100.26.1` |
| 220  | `SOTE-MEDMOB-IOT` | `10.100.27.0/24` | 254 | `10.100.27.1` |

> **Megjegyzés:** A /22-es alhálózatok (~1000 host) az összes campus-eszközt lefedik a csoporton belül.  
> Ha campusonkénti szegmentáció szükséges (BKT/KKT/NET külön), az alhálózatok felezhetők `/23`-ra.

---

#### 2.2.6 OSPF terv — új campus infrastruktúra

| Paraméter | Érték | Indok |
|---|---|---|
| Process ID | `100` | Új, elkülönített process — nem ütközik a meglévő OSPF 1/2-vel |
| Area | `0.0.0.0` (backbone) | HLD hibájának elkerülése — meglévő OSPF 1/2 nem backbone area! |
| Router-ID | Loopback0 (`10.63.75.x`) | Stabil, eszközönként egyedi |
| Network type | `point-to-point` | P2P /30 linken — nincs DR/BDR overhead |
| Hello / Dead | `10s / 40s` (default) | Campus-szintű konvergencia |
| Authentication | MD5 (`SOTE-OSPF-KEY`) | Biztonságos |
| Redistribúció | EC-en: `connected` + `static` → OSPF 100 | Campus útvonalak hirdetése |

---

## 2. fejezet jóváhagyási pont

> ✋ **Kérlek ellenőrizd a fentieket:**
> - Hostname séma (`BKT-EC-1` stb.) — megfelelő?
> - IP tartományok (`10.63.72-76.x`, `10.100.x.x`) — nem ütköznek meglévőkkel?
> - Kliens VLAN subnet méretek (`/22` ill. `/23`) — elegendő a várható eszközszámhoz?
> - OSPF Process 100, Area 0 — megfelelő?
>
> Ha rendben, folytatom a **3. fejezettel: Enterprise Core fizikai összeköttetések + konfiguráció.**

---

*SOTE LLD V0.1 — 1-2. fejezet | 2026-05-19*

---

## 3. Enterprise Core

### 3.1 Eszköz áttekintés

| Hostname | Modell | Helyszín | Szerepkör |
|---|---|---|---|
| `BKT-EC-1` | Cisco Catalyst C9500-48Y4C | BKT Szerverterem | Enterprise Core #1 |
| `BKT-EC-2` | Cisco Catalyst C9500-48Y4C | BKT Szerverterem | Enterprise Core #2 |
| `KKT-EC-1` | Cisco Catalyst C9500-48Y4C | KKT Szerverterem | Enterprise Core #1 |
| `KKT-EC-2` | Cisco Catalyst C9500-48Y4C | KKT Szerverterem | Enterprise Core #2 |

**C9500-48Y4C portok:**
- `TwentyFiveGigE1/0/1–48` — 48× 25G SFP28 (SFP-10G-SR / SFP-10G-LR / SFP-1G-SX)
- `HundredGigE1/0/49–52` — 4× 100G QSFP28 (100G DAC vagy 40G QSFP-40G-SR4)
- `GigabitEthernet0` — dedikált Management port (OOB)

---

### 3.2 Fizikai port-kiosztás

#### BKT-EC-1 port-kiosztás

| Port | Típus | Céleszköz | Cél-port | Médium | SFP |
|---|---|---|---|---|---|
| `Hu1/0/49` | 100G QSFP28 | BKT-EC-2 | Hu1/0/49 | 100G DAC | QSFP28-100G-CU |
| `Hu1/0/50` | 100G QSFP28 | BKT-EC-2 | Hu1/0/50 | 100G DAC | QSFP28-100G-CU |
| `Fo1/0/51` | 40G QSFP+ | BKT-IC-1 | Fo1/0/1 | 40G MMF | QSFP-40G-SR4 |
| `Fo1/0/52` | 40G QSFP+ | BKT-IC-2 | Fo1/0/1 | 40G MMF | QSFP-40G-SR4 |
| `TF1/0/1` | 10G SFP28 | Fortigate BKT | — | 10G MMF (MPO bkt-1) | SFP-10G-SR |
| `TF1/0/2` | 10G SFP28 | Fortigate BKT | — | 10G MMF (MPO bkt-2) | SFP-10G-SR |
| `TF1/0/3–9` | 10G SFP28 | KKT Dist D2 #1–7 | D2-uplink | 10G SMF | SFP-10G-LR |
| `TF1/0/10–20` | 10G SFP28 | BKT Dist D1 #1–11 | D1-uplink | 10G SMF | SFP-10G-LR |
| `TF1/0/47` | 10G SFP28 | BKT-OOB-TSG | Gi1/0/1 | 10G MMF | SFP-10G-SR |
| `GE0` | 1G Mgmt | OOB switch | — | UTP Cat6 | — |

> **Fortigate → EC kapcsolat:** A Fortigate QSFP-40G-SR4 (MPO-12) portjáról MPO→2×LC breakout kábel megy  
> `TF1/0/1` és `TF1/0/2` portokra — ezek Po2 port-channelben futnak (2×10G = 20G LAG a Fortigate felé).

#### BKT-EC-2 port-kiosztás

| Port | Típus | Céleszköz | Cél-port | Médium | SFP |
|---|---|---|---|---|---|
| `Hu1/0/49` | 100G QSFP28 | BKT-EC-1 | Hu1/0/49 | 100G DAC | QSFP28-100G-CU |
| `Hu1/0/50` | 100G QSFP28 | BKT-EC-1 | Hu1/0/50 | 100G DAC | QSFP28-100G-CU |
| `Fo1/0/51` | 40G QSFP+ | BKT-IC-1 | Fo1/0/2 | 40G MMF | QSFP-40G-SR4 |
| `Fo1/0/52` | 40G QSFP+ | BKT-IC-2 | Fo1/0/2 | 40G MMF | QSFP-40G-SR4 |
| `TF1/0/1` | 10G SFP28 | Fortigate BKT | — | 10G MMF (MPO bkt-3) | SFP-10G-SR |
| `TF1/0/2` | 10G SFP28 | Fortigate BKT | — | 10G MMF (MPO bkt-4) | SFP-10G-SR |
| `TF1/0/3–9` | 10G SFP28 | KKT Dist D2 #8–14 | D2-uplink | 10G SMF | SFP-10G-LR |
| `TF1/0/10–20` | 10G SFP28 | BKT Dist D1 #1–11 | D1-uplink | 10G SMF | SFP-10G-LR |
| `TF1/0/47` | 10G SFP28 | BKT-OOB-TSG | Gi1/0/2 | 10G MMF | SFP-10G-SR |
| `GE0` | 1G Mgmt | OOB switch | — | UTP Cat6 | — |

> **KKT-EC-1 és KKT-EC-2:** azonos logika, tükrözve — KKT-EC-1 tart. BKT Dist D2 #1–6, KKT Dist D1 #1–14  
> KKT-EC-2 tart. BKT Dist D2 #7–11, KKT Dist D1 #1–14 (duplikált D1 uplinkok az HA miatt)

> ⚠ **Megjegyzés:** Pontos disztribúciós helyszín ↔ EC port mapping a variáns-specifikus LLD-ben kerül rögzítésre,  
> az optikai felmérés és az épületek tényleges elhelyezkedése alapján.

---

### 3.3 ASCII topológia — Enterprise Core

```
BKT Szerverterem                         KKT Szerverterem
──────────────────────────────────────   ──────────────────────────────────────
  Fortigate BKT                            Fortigate KKT
      │ 2×10G MPO (Po2)                        │ 2×10G MPO (Po2)
      ▼                                         ▼
┌──────────────┐  100G DAC Po1  ┌──────────────┐  ┌──────────────┐  100G DAC Po1  ┌──────────────┐
│  BKT-EC-1   │◄──────────────►│  BKT-EC-2   │  │  KKT-EC-1   │◄──────────────►│  KKT-EC-2   │
└──────────────┘                └──────────────┘  └──────────────┘                └──────────────┘
    │      │                        │      │           │      │                        │      │
   40G    40G                      40G    40G         40G    40G                      40G    40G
  MMF    MMF                      MMF    MMF         MMF    MMF                      MMF    MMF
    │      │                        │      │           │      │                        │      │
    ▼      ▼                        ▼      ▼           ▼      ▼                        ▼      ▼
BKT-IC-1  BKT-IC-2            BKT-IC-1  BKT-IC-2  KKT-IC-1  KKT-IC-2            KKT-IC-1  KKT-IC-2
```

---

### 3.4 IOS-XE konfiguráció — BKT-EC-1

> **Sablon:** BKT-EC-2 / KKT-EC-1 / KKT-EC-2 ugyanígy, az IP-cím tervnek megfelelően cserélt értékekkel.

#### 3.4.1 Alap konfiguráció

```ios
hostname BKT-EC-1
!
ip domain-name sote.hu
ip name-server 10.63.64.2
!
! ── Authentikáció ─────────────────────────────────────────
aaa new-model
aaa authentication login default group tacacs+ local
aaa authorization exec default group tacacs+ local
aaa accounting exec default start-stop group tacacs+
!
username admin privilege 15 algorithm-type sha256 secret <PASSWORD>
!
! ── SSH ───────────────────────────────────────────────────
crypto key generate rsa modulus 4096
ip ssh version 2
ip ssh time-out 60
ip ssh authentication-retries 3
line vty 0 15
 transport input ssh
 login authentication default
 exec-timeout 15 0
!
! ── NTP ───────────────────────────────────────────────────
ntp server 10.63.64.5 prefer
ntp server 10.63.64.6
!
! ── Logging ───────────────────────────────────────────────
logging host 10.63.64.10
logging trap informational
logging source-interface Loopback0
service timestamps log datetime msec localtime
!
! ── SNMP ──────────────────────────────────────────────────
snmp-server community <COMMUNITY-RO> RO
snmp-server location BKT Szerverterem
snmp-server contact netops@sote.hu
snmp-server host 10.63.64.10 version 2c <COMMUNITY-RO>
```

#### 3.4.2 Management interface

```ios
! ── Management (OOB) ──────────────────────────────────────
interface GigabitEthernet0
 description TO-BKT-OOB-TSG-Gi0/0 [OOB-MGMT]
 vrf forwarding Mgmt-vrf
 ip address 10.63.72.10 255.255.255.0
 no shutdown
!
ip route vrf Mgmt-vrf 0.0.0.0 0.0.0.0 10.63.72.1
```

#### 3.4.3 Loopback (Router-ID)

```ios
interface Loopback0
 description ROUTER-ID-OSPF100
 ip address 10.63.75.1 255.255.255.255
 no shutdown
```

#### 3.4.4 EC#1 ↔ EC#2 belső gerinc (Port-Channel)

```ios
! ── EC belső gerinc — Po1 (2×100G DAC) ───────────────────
interface Port-channel1
 description TO-BKT-EC-2-Po1 [BACKBONE-100G]
 no switchport
 ip address 10.63.76.1 255.255.255.252
 ip ospf network point-to-point
 ip ospf 100 area 0
 ip ospf authentication message-digest
 ip ospf message-digest-key 1 md5 <OSPF-KEY>
 no shutdown
!
interface HundredGigE1/0/49
 description TO-BKT-EC-2-Hu1/0/49 [BACKBONE-DAC-1]
 no switchport
 channel-group 1 mode active
 no shutdown
!
interface HundredGigE1/0/50
 description TO-BKT-EC-2-Hu1/0/50 [BACKBONE-DAC-2]
 no switchport
 channel-group 1 mode active
 no shutdown
```

#### 3.4.5 EC → InterConnect uplinkok

```ios
! ── EC#1 → BKT-IC-1 (40G MMF) ────────────────────────────
interface FortyGigabitEthernet1/0/51
 description TO-BKT-IC-1-Fo1/0/1 [BACKBONE-40G]
 no switchport
 ip address 10.63.76.9 255.255.255.252
 ip ospf network point-to-point
 ip ospf 100 area 0
 ip ospf authentication message-digest
 ip ospf message-digest-key 1 md5 <OSPF-KEY>
 no shutdown
!
! ── EC#1 → BKT-IC-2 (40G MMF) ────────────────────────────
interface FortyGigabitEthernet1/0/52
 description TO-BKT-IC-2-Fo1/0/1 [BACKBONE-40G]
 no switchport
 ip address 10.63.76.13 255.255.255.252
 ip ospf network point-to-point
 ip ospf 100 area 0
 ip ospf authentication message-digest
 ip ospf message-digest-key 1 md5 <OSPF-KEY>
 no shutdown
```

#### 3.4.6 EC → Fortigate (Campus ↔ Szerver zóna határ)

```ios
! ── Fortigate felé — Po2 (2×10G MPO breakout) ────────────
interface Port-channel2
 description TO-FORTIGATE-BKT-Po2 [ZONEBORDER-FW]
 no switchport
 ip address 10.63.76.101 255.255.255.252
 no ip ospf 100 area 0
 no shutdown
!
interface TwentyFiveGigE1/0/1
 description TO-FORTIGATE-BKT-MPO-LANE1 [ZONEBORDER-FW]
 no switchport
 channel-group 2 mode active
 no shutdown
!
interface TwentyFiveGigE1/0/2
 description TO-FORTIGATE-BKT-MPO-LANE2 [ZONEBORDER-FW]
 no switchport
 channel-group 2 mode active
 no shutdown
```

> **OSPF Process 1 (meglévő) kiterjesztése:** A Fortigate–EC OSPF szomszédság az  
> existáló OSPF Process 1 (Area 10.10.255.1) keretén belül marad, a BKATA→BKT-EC-1  
> migrációval párhuzamosan konfigurálandó. Az aktuális OSPF 1 router-id és  
> neighborship paraméterek a Fortigate oldalán nem változnak.

#### 3.4.7 Disztribúció uplink portok (D1 lokális + D2 cross-site)

```ios
! ── BKT Dist D1 uplinkok — TF1/0/10-20 (11 BKT helyszín) ─
! Sablon — minden BKT disztribúciós helyszínhez ismétlendő:
interface TwentyFiveGigE1/0/10
 description TO-<EPULET>-DIST-1-TF1/0/uplink [DIST-D1]
 no switchport
 ip address 10.63.76.<X> 255.255.255.252
 ip ospf network point-to-point
 ip ospf 100 area 0
 ip ospf authentication message-digest
 ip ospf message-digest-key 1 md5 <OSPF-KEY>
 no shutdown
!
! ── KKT Dist D2 cross-site uplinkok — TF1/0/3-9 (7 KKT helyszín) ─
! Sablon — minden KKT disztribúciós helyszínhez ismétlendő:
interface TwentyFiveGigE1/0/3
 description TO-<EPULET>-DIST-2-TF1/0/uplink [DIST-D2-CROSSSITE]
 no switchport
 ip address 10.63.76.<Y> 255.255.255.252
 ip ospf network point-to-point
 ip ospf 100 area 0
 ip ospf authentication message-digest
 ip ospf message-digest-key 1 md5 <OSPF-KEY>
 no shutdown
```

> Pontos IP-értékek a disztribúciós helyszín-listával együtt a variáns-specifikus LLD-ben.

#### 3.4.8 OSPF Process 100

```ios
router ospf 100
 router-id 10.63.75.1
 area 0 authentication message-digest
 passive-interface default
 no passive-interface Port-channel1
 no passive-interface FortyGigabitEthernet1/0/51
 no passive-interface FortyGigabitEthernet1/0/52
 no passive-interface TwentyFiveGigE1/0/3
 no passive-interface TwentyFiveGigE1/0/4
 no passive-interface TwentyFiveGigE1/0/5
 no passive-interface TwentyFiveGigE1/0/6
 no passive-interface TwentyFiveGigE1/0/7
 no passive-interface TwentyFiveGigE1/0/8
 no passive-interface TwentyFiveGigE1/0/9
 no passive-interface TwentyFiveGigE1/0/10
 no passive-interface TwentyFiveGigE1/0/11
 no passive-interface TwentyFiveGigE1/0/12
 no passive-interface TwentyFiveGigE1/0/13
 no passive-interface TwentyFiveGigE1/0/14
 no passive-interface TwentyFiveGigE1/0/15
 no passive-interface TwentyFiveGigE1/0/16
 no passive-interface TwentyFiveGigE1/0/17
 no passive-interface TwentyFiveGigE1/0/18
 no passive-interface TwentyFiveGigE1/0/19
 no passive-interface TwentyFiveGigE1/0/20
 network 10.63.75.1 0.0.0.0 area 0
 network 10.63.76.0 0.0.0.255 area 0
 redistribute connected subnets route-map OSPF100-REDIST-CONNECTED
!
ip prefix-list OSPF100-LOOPBACKS seq 10 permit 10.63.75.0/24 le 32
ip prefix-list OSPF100-INFRA    seq 10 permit 10.63.76.0/24 le 30
!
route-map OSPF100-REDIST-CONNECTED permit 10
 match ip address prefix-list OSPF100-LOOPBACKS OSPF100-INFRA
```

#### 3.4.9 Összefoglaló IP-táblázat — BKT Enterprise Core

| Eszköz | Interface | IP | Leírás |
|---|---|---|---|
| BKT-EC-1 | Loopback0 | `10.63.75.1/32` | Router-ID |
| BKT-EC-1 | GE0 (Mgmt-vrf) | `10.63.72.10/24` | OOB Management |
| BKT-EC-1 | Po1 (↔BKT-EC-2) | `10.63.76.1/30` | EC belső gerinc |
| BKT-EC-1 | Fo1/0/51 (↔IC#1) | `10.63.76.9/30` | IC#1 uplink |
| BKT-EC-1 | Fo1/0/52 (↔IC#2) | `10.63.76.13/30` | IC#2 uplink |
| BKT-EC-1 | Po2 (↔Fortigate) | `10.63.76.101/30` | Zónahatár Forti |
| BKT-EC-2 | Loopback0 | `10.63.75.2/32` | Router-ID |
| BKT-EC-2 | GE0 (Mgmt-vrf) | `10.63.72.11/24` | OOB Management |
| BKT-EC-2 | Po1 (↔BKT-EC-1) | `10.63.76.2/30` | EC belső gerinc |
| BKT-EC-2 | Fo1/0/51 (↔IC#1) | `10.63.76.17/30` | IC#1 uplink |
| BKT-EC-2 | Fo1/0/52 (↔IC#2) | `10.63.76.21/30` | IC#2 uplink |
| BKT-EC-2 | Po2 (↔Fortigate) | `10.63.76.105/30` | Zónahatár Forti |
| KKT-EC-1 | Loopback0 | `10.63.75.3/32` | Router-ID |
| KKT-EC-1 | GE0 (Mgmt-vrf) | `10.63.73.10/24` | OOB Management |
| KKT-EC-1 | Po1 (↔KKT-EC-2) | `10.63.76.5/30` | EC belső gerinc |
| KKT-EC-1 | Fo1/0/51 (↔IC#1) | `10.63.76.25/30` | IC#1 uplink |
| KKT-EC-1 | Fo1/0/52 (↔IC#2) | `10.63.76.29/30` | IC#2 uplink |
| KKT-EC-1 | Po2 (↔Fortigate) | `10.63.76.109/30` | Zónahatár Forti |
| KKT-EC-2 | Loopback0 | `10.63.75.4/32` | Router-ID |
| KKT-EC-2 | GE0 (Mgmt-vrf) | `10.63.73.11/24` | OOB Management |
| KKT-EC-2 | Po1 (↔KKT-EC-1) | `10.63.76.6/30` | EC belső gerinc |
| KKT-EC-2 | Fo1/0/51 (↔IC#1) | `10.63.76.33/30` | IC#1 uplink |
| KKT-EC-2 | Fo1/0/52 (↔IC#2) | `10.63.76.37/30` | IC#2 uplink |
| KKT-EC-2 | Po2 (↔Fortigate) | `10.63.76.113/30` | Zónahatár Forti |

---

## 3. fejezet jóváhagyási pont

> ✋ **Kérlek ellenőrizd a következőket:**
> - Port-kiosztás elfogadható? (QSFP28 49-52 az IC/EC gerinc, SFP28 1-2 a Fortigate, 3-20 dist uplinkok)
> - Fortigate–EC kapcsolat: Po2 (2×10G MPO breakout LAG) — megfelelő, vagy más megközelítés?
> - OSPF 100 Area 0, MD5 autentikáció — rendben?
> - IP-cím értékek (10.63.76.x sorozat) — rendben?
>
> Ha rendben, folytatom a **4. fejezettel: InterConnect réteg fizikai összeköttetések + konfiguráció.**

---

*SOTE LLD V0.1 — 1-3. fejezet | 2026-05-19*
