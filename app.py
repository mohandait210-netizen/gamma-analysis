/* ============================================
   GEX ANALYSER — Dark Finance Theme
   Bloomberg Terminal meets Modern Quant
   ============================================ */

@import url('https://fonts.googleapis.com/css2?family=IBM+Plex+Mono:wght@400;600&family=Syne:wght@400;700;800&display=swap');

:root {
  --bg-primary:    #090c10;
  --bg-card:       #0e1318;
  --bg-hover:      #141b22;
  --border:        #1e2d3d;
  --accent-green:  #00ff9d;
  --accent-red:    #ff3c5a;
  --accent-orange: #ff9a00;
  --accent-blue:   #00aaff;
  --text-primary:  #e8f0f7;
  --text-muted:    #5a7a94;
  --text-dim:      #2e4a5e;
  --glow-green:    0 0 20px rgba(0,255,157,0.25);
  --glow-red:      0 0 20px rgba(255,60,90,0.25);
}

/* ---- BASE ---- */
html, body, [class*="css"] {
  background-color: var(--bg-primary) !important;
  color: var(--text-primary) !important;
  font-family: 'Syne', sans-serif !important;
}

/* ---- HEADER ---- */
h1 {
  font-family: 'Syne', sans-serif !important;
  font-weight: 800 !important;
  font-size: 2rem !important;
  letter-spacing: -0.03em !important;
  color: var(--text-primary) !important;
  border-bottom: 1px solid var(--border) !important;
  padding-bottom: 1rem !important;
  margin-bottom: 1.5rem !important;
}
h1::before {
  content: "▶ ";
  color: var(--accent-green);
  font-size: 1.2rem;
}

h2, h3 {
  font-family: 'IBM Plex Mono', monospace !important;
  font-weight: 600 !important;
  color: var(--accent-blue) !important;
  text-transform: uppercase !important;
  letter-spacing: 0.08em !important;
  font-size: 0.85rem !important;
}

/* ---- SIDEBAR ---- */
section[data-testid="stSidebar"] {
  background: var(--bg-card) !important;
  border-right: 1px solid var(--border) !important;
}

/* ---- FILE UPLOADER ---- */
[data-testid="stFileUploader"] {
  background: var(--bg-card) !important;
  border: 1px dashed var(--border) !important;
  border-radius: 8px !important;
  padding: 1.5rem !important;
  transition: border-color 0.2s !important;
}
[data-testid="stFileUploader"]:hover {
  border-color: var(--accent-blue) !important;
}

/* ---- INFO / SUCCESS / WARNING BOXES ---- */
[data-testid="stAlert"] {
  background: var(--bg-card) !important;
  border-radius: 6px !important;
  border-left-width: 3px !important;
  font-family: 'IBM Plex Mono', monospace !important;
  font-size: 0.85rem !important;
}
/* Info → blue */
[data-testid="stAlert"][kind="info"] {
  border-left-color: var(--accent-blue) !important;
}
/* Success → green */
[data-testid="stAlert"][kind="success"] {
  border-left-color: var(--accent-green) !important;
  box-shadow: var(--glow-green) !important;
}
/* Warning → orange */
[data-testid="stAlert"][kind="warning"] {
  border-left-color: var(--accent-orange) !important;
}
/* Error → red */
[data-testid="stAlert"][kind="error"] {
  border-left-color: var(--accent-red) !important;
  box-shadow: var(--glow-red) !important;
}

/* ---- DATAFRAME / TABLE ---- */
[data-testid="stDataFrame"] {
  background: var(--bg-card) !important;
  border: 1px solid var(--border) !important;
  border-radius: 8px !important;
  font-family: 'IBM Plex Mono', monospace !important;
  font-size: 0.82rem !important;
}
[data-testid="stDataFrame"] th {
  background: var(--bg-hover) !important;
  color: var(--accent-blue) !important;
  text-transform: uppercase !important;
  letter-spacing: 0.06em !important;
  font-size: 0.75rem !important;
  border-bottom: 1px solid var(--border) !important;
}
[data-testid="stDataFrame"] td {
  color: var(--text-primary) !important;
  border-bottom: 1px solid var(--border) !important;
}

/* ---- SLIDER ---- */
[data-testid="stSlider"] > div > div > div {
  background: var(--accent-blue) !important;
}
[data-testid="stSlider"] label {
  font-family: 'IBM Plex Mono', monospace !important;
  font-size: 0.8rem !important;
  color: var(--text-muted) !important;
  text-transform: uppercase !important;
  letter-spacing: 0.06em !important;
}

/* ---- NUMBER INPUT ---- */
[data-testid="stNumberInput"] input {
  background: var(--bg-card) !important;
  border: 1px solid var(--border) !important;
  border-radius: 6px !important;
  color: var(--accent-green) !important;
  font-family: 'IBM Plex Mono', monospace !important;
  font-size: 1.1rem !important;
  font-weight: 600 !important;
  padding: 0.5rem 1rem !important;
  transition: border-color 0.2s !important;
}
[data-testid="stNumberInput"] input:focus {
  border-color: var(--accent-green) !important;
  box-shadow: var(--glow-green) !important;
  outline: none !important;
}

/* ---- TEXT AREA (copy boxes) ---- */
textarea {
  background: var(--bg-card) !important;
  border: 1px solid var(--border) !important;
  border-radius: 6px !important;
  color: var(--accent-orange) !important;
  font-family: 'IBM Plex Mono', monospace !important;
  font-size: 0.82rem !important;
  resize: none !important;
}
textarea:focus {
  border-color: var(--accent-orange) !important;
  outline: none !important;
}

/* ---- BUTTONS ---- */
button[kind="primary"], .stButton > button {
  background: transparent !important;
  border: 1px solid var(--accent-green) !important;
  color: var(--accent-green) !important;
  font-family: 'IBM Plex Mono', monospace !important;
  font-size: 0.8rem !important;
  font-weight: 600 !important;
  text-transform: uppercase !important;
  letter-spacing: 0.1em !important;
  border-radius: 4px !important;
  padding: 0.5rem 1.5rem !important;
  transition: all 0.2s !important;
}
.stButton > button:hover {
  background: var(--accent-green) !important;
  color: var(--bg-primary) !important;
  box-shadow: var(--glow-green) !important;
}

/* ---- MATPLOTLIB CHARTS — force dark bg ---- */
[data-testid="stImage"] img,
canvas {
  border-radius: 8px !important;
  border: 1px solid var(--border) !important;
}

/* ---- DIVIDER ---- */
hr {
  border-color: var(--border) !important;
}

/* ---- SCROLLBAR ---- */
::-webkit-scrollbar { width: 6px; height: 6px; }
::-webkit-scrollbar-track { background: var(--bg-primary); }
::-webkit-scrollbar-thumb { background: var(--border); border-radius: 3px; }
::-webkit-scrollbar-thumb:hover { background: var(--accent-blue); }

/* ---- TICKER STRIP (optionnel) ---- */
.ticker-strip {
  font-family: 'IBM Plex Mono', monospace;
  font-size: 0.75rem;
  color: var(--text-muted);
  border-top: 1px solid var(--border);
  padding: 0.4rem 0;
  letter-spacing: 0.05em;
}
