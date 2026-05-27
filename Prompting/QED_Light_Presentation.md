# Quantum Electrodynamics, Light, and the Speed of Light
### A Physicist's Tutorial Presentation

---

## Table of Contents

1. [The Road to QED — A 100-Year Arc](#1-the-road-to-qed)
2. [Light as a Quantum Field — The Photon](#2-light-as-a-quantum-field)
3. [Why Photons Are Massless — Gauge Symmetry](#3-gauge-symmetry-u1)
4. [The Speed of Light in QED — Why c Is What It Is](#4-speed-of-light-in-qed)
5. [Feynman's Sum-Over-Paths — How Light Really Travels](#5-feynman-path-integral)
6. [Virtual vs. Real Photons — What Actually Mediates Forces](#6-virtual-vs-real-photons)
7. [The Fine Structure Constant α — The Number That Rules EM](#7-fine-structure-constant)
8. [The Quantum Vacuum and Light Propagation](#8-quantum-vacuum)
9. [QED's Greatest Triumphs — Predictions vs. Experiment](#9-experimental-triumphs)
10. [Modern Frontiers and Open Questions](#10-modern-frontiers)

---

## 1. The Road to QED

### 1.1 The Three Revolutions That Had to Merge

| Revolution | Year | What It Gave Us |
|---|---|---|
| Maxwell's Electrodynamics | 1865 | **c** = 1/√(ε₀μ₀) ≈ 3×10⁸ m/s; light is EM waves |
| Special Relativity (Einstein) | 1905 | Space-time unification; c is invariant for **all** observers |
| Quantum Mechanics (Planck, Bohr, Heisenberg, Schrödinger) | 1900–1926 | Energy is quantized; particles have wave nature |

**The problem:** Maxwell + Special Relativity works. Quantum Mechanics + Special Relativity = disaster (negative probabilities, indefinite particle number). A fundamentally new framework was needed.

### 1.2 Dirac's Equation (1928) — The First Seed

Dirac sought a wave equation **linear** in both ∂/∂t and ∇ to satisfy special relativity:

```
(iγᵘ∂ᵤ − mc/ℏ)ψ = 0
```

- Correctly predicted electron spin as a **relativistic necessity**, not a postulate.
- Predicted **antiparticles** (positron, discovered 1932).
- But still a **single-particle** equation — it breaks down when pair creation is possible.

### 1.3 QED Is Born (1940s)

The founders of QED:

| Physicist | Contribution |
|---|---|
| **Richard Feynman** | Path integral formulation, Feynman diagrams, intuitive pictorial rules |
| **Julian Schwinger** | Rigorous operator formalism, renormalization |
| **Sin-Itiro Tomonaga** | Independent covariant formulation |
| **Freeman Dyson** | Proved all three approaches are equivalent |

Nobel Prize 1965: Feynman, Schwinger, Tomonaga.

> **Core insight:** We must promote the electromagnetic field **and** the electron field to quantum operators. Particles are *excitations* of underlying quantum fields.

---

## 2. Light as a Quantum Field

### 2.1 The Electromagnetic Field as a Quantum Object

In classical EM, we have the 4-potential **Aᵘ = (φ/c, A)** satisfying Maxwell's equations. QED **quantizes** this field.

The free electromagnetic Lagrangian density:

```
ℒ_EM = −(1/4) FᵘᵛFᵤᵥ
```

where the field-strength tensor:

```
Fᵘᵛ = ∂ᵘAᵛ − ∂ᵛAᵘ
```

Quantizing this field gives **photons** — discrete quanta of the EM field.

### 2.2 What Is a Photon, Precisely?

A photon is an **elementary excitation of the quantum electromagnetic field** with:

| Property | Value | Significance |
|---|---|---|
| Mass | 0 | Must travel at exactly c; no rest frame exists |
| Spin | 1 (vector boson) | Two polarization states (transverse only) |
| Charge | 0 | Does not interact with itself at tree level |
| Helicity | ±ℏ | Left- and right-circular polarization |

The field operator (simplified, 1D):

```
Â(x,t) = Σₖ √(ℏ/2ωₖV) [aₖ e^{i(kx−ωt)} + aₖ† e^{−i(kx−ωt)}]
```

- **aₖ** : annihilation operator — removes one photon of momentum ℏk
- **aₖ†** : creation operator — adds one photon of momentum ℏk
- A laser beam = **coherent state** of photons (eigenstate of â)

### 2.3 The Photon Number Is NOT Always Defined

One of QED's profound lessons: in a coherent state (classical light), **photon number is maximally uncertain**. The uncertainty relation:

```
ΔN · Δφ ≥ 1/2
```

A classical plane wave has definite phase φ → completely indefinite photon number N. A Fock state (N photons) has completely indefinite phase.

---

## 3. Gauge Symmetry U(1) — Why Photons Are Massless

### 3.1 The Deep Reason

The photon's mass is **exactly zero** — not approximately, not coincidentally. This is protected by a fundamental symmetry: **local U(1) gauge invariance**.

The full QED Lagrangian:

```
ℒ_QED = ψ̄(iγᵘDᵤ − mc/ℏ)ψ − (1/4)FᵘᵛFᵤᵥ
```

where the **covariant derivative** is:

```
Dᵤ = ∂ᵤ + i(e/ℏc)Aᵤ
```

### 3.2 The Gauge Transformation

This Lagrangian is invariant under the **local** transformation:

```
ψ(x) → e^{iα(x)} ψ(x)
Aᵤ(x) → Aᵤ(x) − (ℏc/e) ∂ᵤα(x)
```

where α(x) is **any** smooth function of spacetime.

### 3.3 Why This Forces Zero Photon Mass

A photon mass term would look like:

```
ℒ_mass = (1/2)(m_γ c/ℏ)² AᵘAᵤ
```

But under a gauge transformation: Aᵤ → Aᵤ + ∂ᵤα, so AᵘAᵤ → (Aᵘ + ∂ᵘα)(Aᵤ + ∂ᵤα) ≠ AᵘAᵤ

The mass term breaks gauge invariance. Therefore: **gauge symmetry ⟹ m_γ = 0 exactly.**

> **Ward–Takahashi Identity:** Even at all orders of perturbation theory (loop corrections), gauge invariance protects the photon from acquiring mass. The photon self-energy Πᵘᵛ(q) is always transverse: qᵤΠᵘᵛ = 0.

### 3.4 Current Experimental Bound

```
m_γ < 10⁻²⁷ eV/c² (Particle Data Group, 2024)
```

This is 22 orders of magnitude smaller than the electron mass. For all practical and theoretical purposes: **m_γ = 0 exactly**.

---

## 4. The Speed of Light in QED — Why c Is What It Is

### 4.1 c Is Not the "Speed of Light" — It Is the Speed of Causality

In modern physics, c is best understood as the **maximum speed of information transfer** — the conversion factor between space and time in Minkowski spacetime:

```
ds² = c²dt² − dx² − dy² − dz²
```

Massless particles (like photons) travel on **null geodesics** where ds² = 0:

```
ds² = 0 ⟹ c²dt² = dx² + dy² + dz²  ⟹  |v| = c
```

This is a **geometric consequence** of having zero rest mass, not a special property of electromagnetic radiation.

### 4.2 From Maxwell to c — The Classical Derivation

In vacuum, Maxwell's equations give:

```
∇²E = ε₀μ₀ ∂²E/∂t²
```

This is a wave equation with phase velocity:

```
c = 1/√(ε₀μ₀) ≈ 299,792,458 m/s
```

In QED, ε₀ and μ₀ arise from the **coupling constant** e and the structure of the vacuum. The fine structure constant α = e²/(4πε₀ℏc) ≈ 1/137 encodes the strength of the EM interaction.

### 4.3 Is c Constant in the Quantum Vacuum?

**Tree level (no loops):** Photons travel at exactly c in vacuum.

**Loop level:** Virtual electron-positron pairs cause the vacuum to act as a **polarizable medium**. This leads to:

- **Vacuum birefringence** in strong magnetic fields (predicted by QED, confirmed 2017 for neutron stars)
- **Light-by-light scattering** (γ + γ → γ + γ, confirmed at LHC 2017)
- A tiny **effective refractive index** n > 1 in intense fields

The QED effective Lagrangian in strong fields (Euler-Heisenberg):

```
ℒ_EH = ℒ_Maxwell + (α²/90π²)(ℏ³/m⁴c⁵) [4(E² − c²B²)² + 7c²(E·B)²] + ...
```

For fields below the Schwinger critical field E_c = m²c³/eℏ ≈ 1.3 × 10¹⁸ V/m, these corrections are negligibly small. Light travels at c to extraordinary precision in all everyday contexts.

### 4.4 c in Special Relativity and QED — Unified View

| Framework | Role of c |
|---|---|
| Special Relativity | Invariant speed; unifies space and time |
| Maxwell EM | Phase velocity of EM waves in vacuum |
| QED | Speed of massless gauge boson; set by Lorentz invariance of the action |
| Planck units | c = 1 (absorbed into geometry) |

> In Planck units (ℏ = c = G = 1), c is not a "speed" at all — it is dimensionless 1, encoding the geometry of spacetime. The "speed of light" is really the statement that our universe has a Lorentzian metric signature (−,+,+,+).

---

## 5. Feynman's Sum-Over-Paths — How Light Really Travels

### 5.1 The Path Integral Formulation

Feynman's deep insight: a quantum particle does not travel a single path. It **simultaneously explores all possible paths**. The probability amplitude for going from A to B is:

```
⟨B|A⟩ = ∫ 𝒟[paths] e^{iS[path]/ℏ}
```

where S[path] is the **classical action** for that path. Every path contributes a phase factor e^{iS/ℏ}.

### 5.2 Why Light Appears to Travel in Straight Lines

For a photon traveling from source S to detector D via all possible routes:

- **Near the classical path:** Action S varies slowly → phases nearly aligned → **constructive interference**
- **Far from classical path:** Action S varies rapidly → phases cancel → **destructive interference**

This is the **principle of stationary phase**, which reproduces Fermat's principle of least time as the classical limit (ℏ → 0).

```
δS = 0  ⟺  classical path  ⟺  light travels in straight lines
```

> Feynman's punchline: "Light doesn't really travel in straight lines — it samples all paths. It only *appears* to travel in straight lines because the non-classical paths cancel out."

### 5.3 Feynman Diagrams — Perturbation Theory Visualized

QED is solved perturbatively in powers of α ≈ 1/137. Each order is represented by a Feynman diagram:

**Rules for drawing QED diagrams:**
- **Straight lines (arrows):** Electrons/positrons (fermion propagator)
- **Wavy lines:** Photons (boson propagator)
- **Vertices:** Electron-photon interaction; each vertex contributes a factor of **−ie γᵘ** and a factor of **√α** to the amplitude

**Electron-photon vertex (the fundamental QED interaction):**

```
        e⁻ ────────●──────── e⁻
                   |
                   ~ (photon)
```

Each vertex carries coupling: **e = √(4πα) · √(ε₀ℏc)**

**Compton Scattering** (γ + e⁻ → γ + e⁻) at lowest order:

```
 e⁻ ───────●───────────●─────── e⁻
           |           |
           ~           ~
           γ(in)      γ(out)
```

The amplitude M scales as e² ~ α. The cross section scales as α².

### 5.4 Why Perturbation Theory Works in QED

α ≈ 1/137.036 ≪ 1

Each additional loop adds a factor of α/π ≈ 0.0023. Series converges rapidly:

```
A = A₀ + A₁(α/π) + A₂(α/π)² + A₃(α/π)³ + ...
```

This is why QED is the **most precisely tested theory in all of physics**.

---

## 6. Virtual vs. Real Photons

### 6.1 Real Photons

A real photon obeys the **on-shell condition**:

```
pᵘpᵤ = (E/c)² − |p|² = m²c² = 0
```

That is: E = |p|c. Real photons:
- Travel at exactly c
- Can be detected (they carry energy and momentum away to infinity)
- Have definite helicity (spin ±1 along propagation direction)
- Cannot have longitudinal polarization

### 6.2 Virtual Photons

A virtual photon is an **internal line** in a Feynman diagram — a mathematical tool encoding the quantum propagation of the EM field between interaction vertices. It does **not** satisfy E = |p|c.

The virtual photon **propagator** in Feynman gauge:

```
Dᵘᵛ(q) = −igᵘᵛ / (q² + iε)
```

where q² = (E/c)² − |q|² can be **anything** — positive, negative, or zero.

This off-shell freedom is precisely what allows:
- **Static electric and magnetic fields** (q² < 0, spacelike virtual photons)
- **Bound states** (atoms)
- **Coulomb interaction** (Coulomb scattering is mediated by a spacelike virtual photon)

### 6.3 The Coulomb Force — Virtual Photons at Work

The electrostatic repulsion between two electrons is, in QED, the tree-level exchange of **one virtual photon**:

```
e⁻ ──────●──────────────── e⁻
          |
          ~~~~ (virtual γ, q² < 0)
          |
e⁻ ──────●──────────────── e⁻
```

The Born approximation gives the Coulomb potential:

```
V(r) = e²/(4πε₀r)
```

The 1/r potential emerges from the **Fourier transform of the propagator 1/q²** in 3D momentum space.

> **Profound point:** "Forces" are not fundamental — they are emergent phenomena from **quantum field exchange**. The electromagnetic force is the macroscopic shadow of photon exchange.

---

## 7. The Fine Structure Constant α

### 7.1 Definition

```
α = e² / (4πε₀ℏc) ≈ 1/137.035999084(21)
```

This dimensionless number is the **coupling strength** of the electromagnetic interaction. It characterizes how strongly charged particles interact with the photon field.

### 7.2 Why α Controls Everything in QED

| Phenomenon | α-dependence |
|---|---|
| Hydrogen energy levels | E_n = −α²m_ec²/2n² |
| Fine structure splitting | ~ α⁴ |
| Lamb shift | ~ α⁵ ln(1/α) |
| Hyperfine structure | ~ α⁴(m_e/m_p) |
| Thomson cross section | σ ~ α²/m_e² |
| Electron g-factor anomaly | ~ α/π |

### 7.3 Running of α — It Changes with Energy

α is not a fixed number — it **runs** with the energy scale Q due to vacuum polarization (virtual e⁺e⁻ pairs screen the charge):

```
α(Q²) = α(0) / [1 − (α/3π) ln(Q²/m_e²c⁴) + ...]
```

| Energy Scale | α |
|---|---|
| Q = 0 (Thomson limit) | 1/137.036 |
| Q = m_e c² (0.511 MeV) | ≈ 1/137.0 |
| Q = m_Z c² (91.2 GeV) | ≈ 1/128.9 |

At very high energies, α approaches O(1) and perturbation theory eventually breaks down — but this occurs far beyond current experimental reach.

### 7.4 Why Is α ≈ 1/137?

**We do not know.** This is one of the deepest open questions in physics.

Richard Feynman wrote:
> *"It has been a mystery ever since it was discovered more than fifty years ago, and all good theoretical physicists put this number up on their wall and worry about it."*

---

## 8. The Quantum Vacuum and Light Propagation

### 8.1 The Vacuum Is Not Empty

In QED, the vacuum state |0⟩ is **not** a state of nothingness. It is the ground state of the quantum field, filled with:

- **Zero-point fluctuations** of the EM field: ⟨0|E²|0⟩ ≠ 0
- **Virtual particle-antiparticle pairs** constantly appearing and annihilating
- A non-zero **vacuum energy density**

### 8.2 Casimir Effect — Vacuum Forces Between Conductors

Two uncharged conducting plates separated by distance d experience an **attractive force per unit area**:

```
P_Casimir = −(π²ℏc) / (240 d⁴)
```

For d = 100 nm: P ≈ 1.3 × 10⁻⁴ N/m² (measured to ~1% precision)

This is a **direct consequence** of photon zero-point fluctuations being modified by boundary conditions. Confirmed experimentally to high precision.

### 8.3 Lamb Shift — Vacuum Fluctuations Affect Atomic Spectra

Without QED loop effects, the 2s₁/₂ and 2p₁/₂ states of hydrogen are **exactly degenerate** (Dirac equation prediction). QED predicts they should be split by:

```
ΔE_Lamb = 1057.859 MHz  (QED prediction, to 10+ significant figures)
```

Measured value (Lamb & Retherford, 1947):

```
ΔE_Lamb = 1057.77 ± 0.10 MHz
```

The split arises from the electron interacting with vacuum fluctuations of the EM field, which slightly shifts the 2s energy. This was the first experimental evidence demanding QED's renormalized loop corrections.

### 8.4 Spontaneous Emission — The Vacuum Forces the Atom to Radiate

An atom in an excited state **must** eventually emit a photon even in the absence of any incoming radiation. Why? Because the quantum vacuum fluctuations of the EM field act as a **perturbation** that stimulates the transition.

```
Rate A = (e²ω³|r₁₂|²) / (3πε₀ℏc³)   [Einstein A coefficient, derived from QED]
```

> An atom in "empty space" is never truly isolated — it is always coupled to the vacuum fluctuations of the QED field.

---

## 9. QED's Greatest Triumphs — Predictions vs. Experiment

QED is the most precisely tested theory in the history of science.

### 9.1 Electron Anomalous Magnetic Moment (g−2)

The Dirac equation predicts g = 2 exactly (gyromagnetic ratio). QED predicts corrections:

```
a_e = (g−2)/2 = α/(2π) − 0.328478(α/π)² + 1.1812(α/π)³ − 1.9144(α/π)⁴ + ...
```

| Quantity | Value |
|---|---|
| QED Theory | 0.001 159 652 181 643 (764) |
| Experiment | 0.001 159 652 180 73 (28) |
| Agreement | **12 significant figures** |

This is the most precise agreement between theory and experiment in all of science — equivalent to measuring the distance from New York to Los Angeles to within the width of a human hair.

### 9.2 Hydrogen Lamb Shift

```
Theory:   1057.8514 ± 0.0019 MHz
Experiment: 1057.845 ± 0.009 MHz
```

### 9.3 Light-by-Light Scattering

Predicted by QED: two photons can scatter off each other (γ + γ → γ + γ) via a virtual electron box diagram. This is a purely quantum effect with no classical analogue.

**First direct observation:** ATLAS experiment at LHC, 2017 (Pb-Pb ultra-peripheral collisions)

### 9.4 Vacuum Birefringence

QED predicts that a strong magnetic field makes the vacuum birefringent (different refractive indices for different photon polarizations). Observed in 2017 via polarized X-ray emission from neutron star RX J1856.5−3754 (ESO VLT).

### 9.5 Summary Table

| QED Prediction | Agreement |
|---|---|
| Electron g−2 | 12 significant figures |
| Muon g−2 | 10 significant figures (slight tension at 4.2σ) |
| Lamb shift (H) | 10 significant figures |
| Compton scattering | Excellent |
| Bhabha scattering | Excellent |
| Casimir effect | ~1% |
| Light-by-light scattering | Confirmed 2017 |
| Vacuum birefringence | Confirmed 2017 |

---

## 10. Modern Frontiers and Open Questions

### 10.1 The Muon g−2 Anomaly

The muon anomalous magnetic moment shows a **~4.2σ deviation** between QED+SM prediction and experiment (Fermilab g-2 experiment, 2023):

```
a_μ^exp  = 116 592 059 × 10⁻¹¹
a_μ^theory = 116 591 810 × 10⁻¹¹
```

Δa_μ ≈ 249 × 10⁻¹¹ — potentially a sign of **physics beyond the Standard Model**.

### 10.2 Proton Charge Radius Puzzle

The proton radius measured via the Lamb shift in **muonic hydrogen** (μp atom) disagrees by ~5σ with measurements in regular hydrogen. Partially resolved but still debated, pointing to possible QED corrections at short distances.

### 10.3 Strong-Field QED

In sufficiently strong electric fields (E ≈ E_Schwinger = m²c³/eℏ ≈ 1.3 × 10¹⁸ V/m), the vacuum itself becomes unstable and spontaneously produces real e⁺e⁻ pairs from nothing (**Schwinger pair production**):

```
Rate ~ exp(−πE_c/E)
```

This has not yet been observed directly (requires ~10 × current laser technology). ELI (Extreme Light Infrastructure) aims to approach this regime.

### 10.4 QED Meets Gravity — An Unsolved Problem

QED is a flat-spacetime theory. Combining it with general relativity (curved spacetime) leads to:

- **Hawking radiation** — black holes emit thermal radiation of photons (semi-classical QED on curved background)
- **Unruh effect** — an accelerating observer sees the Minkowski vacuum as a thermal photon bath
- Full quantum gravity remains unsolved

### 10.5 What QED Does Not Explain

| Open Question | Status |
|---|---|
| Why α ≈ 1/137? | Unknown — no derivation from first principles |
| Why 3 generations of fermions? | Unknown |
| Why is e (electron charge) what it is? | Unknown |
| Magnetic monopoles? | Not observed; predicted by grand unified theories |
| Photon truly massless to all orders? | Protected by gauge symmetry — believed yes |

---

## Key Equations Reference

```
QED Lagrangian:
  ℒ_QED = ψ̄(iγᵘ∂ᵤ − mc/ℏ)ψ − eψ̄γᵘAᵤψ − (1/4)FᵘᵛFᵤᵥ

Photon dispersion (real):
  E = |p|c     (massless: m_γ = 0)

Fine structure constant:
  α = e²/(4πε₀ℏc) ≈ 1/137.036

Electron g-factor (QED):
  g/2 = 1 + α/(2π) − 0.3285(α/π)² + ...

Lamb shift (leading QED contribution):
  ΔE_Lamb ~ α⁵ m_e c² (α/π) ln(1/α)

Casimir pressure:
  P = −π²ℏc / (240 d⁴)

Schwinger critical field:
  E_c = m²c³/(eℏ) ≈ 1.3 × 10¹⁸ V/m

Running coupling:
  α(Q²) ≈ α₀ / [1 − (α₀/3π) ln(Q²/m_e²c⁴)]
```

---

## Recommended Reading

**Introductory:**
- Feynman, R.P. — *QED: The Strange Theory of Light and Matter* (1985) — the best popular account ever written
- Zee, A. — *Fearful Symmetry* (1986)

**Advanced Undergraduate:**
- Griffiths, D. — *Introduction to Elementary Particles* (Ch. 9)
- Halzen & Martin — *Quarks and Leptons*

**Graduate:**
- Peskin & Schroeder — *An Introduction to Quantum Field Theory*
- Weinberg — *The Quantum Theory of Fields, Vol. I*
- Srednicki — *Quantum Field Theory* (free online)

**Review Articles:**
- Gabrielse et al., *Physical Review Letters* (2023) — electron g-2 measurement
- ATLAS Collaboration, *Nature Physics* (2017) — light-by-light scattering
- Mignani et al., *MNRAS* (2017) — vacuum birefringence in neutron star

---

*Presentation compiled for physics tutorial use. All equations in SI units unless noted. QED predictions cited at state-of-the-art loop order.*
