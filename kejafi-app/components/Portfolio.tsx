export default function Portfolio() {
  const stats = [
    { val: '$193,486', lbl: 'Total Portfolio Value', accent: 'var(--teal)', border: 'var(--teal)' },
    { val: '11.2%', lbl: 'Expected Annual Return', accent: 'var(--white)', border: 'var(--teal)' },
    { val: '0.77', lbl: 'Sharpe Ratio', accent: 'var(--white)', border: 'var(--teal)' },
    { val: '32%', lbl: 'VaR Reduction (Diversification)', accent: 'var(--green)', border: 'var(--green)' },
    { val: '−12.8%', lbl: 'VaR 95% (Monte Carlo)', accent: 'var(--red)', border: 'var(--red)' },
    { val: '50/100', lbl: 'Diversification Score', accent: '#F5A623', border: '#F5A623' },
  ]

  const mcBars = [
    { l: 'Mean Return', v: 72, c: 'var(--green)', val: '11.2%' },
    { l: 'Volatility', v: 80, c: '#F5A623', val: '14.5%' },
    { l: 'VaR 95%', v: 55, c: 'var(--red)', val: '−12.8%' },
    { l: 'P(Loss)', v: 44, c: 'var(--red)', val: '22.2%' },
    { l: 'Sharpe Ratio', v: 77, c: 'var(--teal)', val: '0.77' },
  ]

  // Simple histogram data
  const hist = [4,6,9,14,22,35,52,68,78,85,88,90,88,84,78,68,55,42,30,20,13,8,5,3]

  return (
    <section id="portfolio" style={{ padding: '96px 48px', background: 'var(--off)', color: 'var(--navy)' }}>
      <div style={{ marginBottom: '56px' }}>
        <div style={{ fontSize: '11px', color: 'var(--teal)', fontFamily: "'DM Mono',monospace", letterSpacing: '2px', textTransform: 'uppercase', marginBottom: '16px' }}>Stage 3</div>
        <h2 style={{ fontFamily: "'Playfair Display',serif", fontSize: 'clamp(32px,5vw,48px)', fontWeight: 700, color: 'var(--navy)', marginBottom: '12px' }}>Portfolio Analytics</h2>
        <p style={{ fontSize: '16px', color: 'var(--gray)', maxWidth: '560px', lineHeight: 1.7, fontWeight: 300 }}>
          Institutional-grade risk analytics powered by Monte Carlo simulation across 10,000 scenarios with correlated return shocks.
        </p>
      </div>

      <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '32px' }}>
        {/* Left col */}
        <div style={{ display: 'flex', flexDirection: 'column', gap: '20px' }}>
          {/* Stat grid */}
          <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '14px' }}>
            {stats.map(({ val, lbl, accent, border }) => (
              <div key={lbl} style={{
                background: 'var(--white)', borderRadius: '12px', padding: '20px',
                boxShadow: '0 2px 12px rgba(0,0,0,0.06)',
                borderLeft: `3px solid ${border}`
              }}>
                <div style={{ fontFamily: "'Playfair Display',serif", fontSize: '28px', color: accent }}>{val}</div>
                <div style={{ fontSize: '11px', color: 'var(--gray)', marginTop: '4px' }}>{lbl}</div>
              </div>
            ))}
          </div>

          {/* Allocation */}
          <div style={{ background: 'var(--white)', borderRadius: '12px', padding: '24px', boxShadow: '0 2px 12px rgba(0,0,0,0.06)' }}>
            <h4 style={{ fontSize: '13px', fontWeight: 600, color: 'var(--navy)', marginBottom: '16px' }}>Portfolio Allocation</h4>
            <div style={{ height: '12px', borderRadius: '6px', overflow: 'hidden', display: 'flex', marginBottom: '12px' }}>
              <div style={{ width: '35.4%', background: 'var(--teal)' }} />
              <div style={{ width: '64.6%', background: 'var(--navy)' }} />
            </div>
            <div style={{ display: 'flex', gap: '20px' }}>
              {[
                { c: 'var(--teal)', l: 'FINE5 Charlotte', v: '35.4% · $68,496' },
                { c: 'var(--navy)', l: 'FINE6 Austin', v: '64.6% · $124,990' },
              ].map(({ c, l, v }) => (
                <div key={l} style={{ display: 'flex', alignItems: 'center', gap: '6px', fontSize: '12px', color: 'var(--gray)' }}>
                  <div style={{ width: '8px', height: '8px', borderRadius: '50%', background: c, flexShrink: 0 }} />
                  {l} — {v}
                </div>
              ))}
            </div>
          </div>
        </div>

        {/* Right col */}
        <div style={{ display: 'flex', flexDirection: 'column', gap: '20px' }}>
          {/* Monte Carlo */}
          <div style={{ background: 'var(--white)', borderRadius: '12px', padding: '24px', boxShadow: '0 2px 12px rgba(0,0,0,0.06)' }}>
            <h4 style={{ fontSize: '13px', fontWeight: 600, color: 'var(--navy)', marginBottom: '16px' }}>Monte Carlo Distribution (10,000 scenarios)</h4>

            {/* Histogram */}
            <div style={{ display: 'flex', alignItems: 'flex-end', gap: '3px', height: '64px', marginBottom: '16px' }}>
              {hist.map((h, i) => (
                <div
                  key={i}
                  style={{
                    flex: 1, borderRadius: '2px 2px 0 0',
                    height: `${h}%`,
                    background: i < 5 ? 'rgba(255,90,95,0.7)' : 'rgba(0,180,204,0.6)',
                    minWidth: '6px'
                  }}
                />
              ))}
            </div>

            <div style={{ display: 'flex', flexDirection: 'column', gap: '10px' }}>
              {mcBars.map(({ l, v, c, val }) => (
                <div key={l} style={{ display: 'flex', alignItems: 'center', gap: '10px' }}>
                  <div style={{ fontSize: '11px', color: 'var(--gray)', width: '90px', flexShrink: 0 }}>{l}</div>
                  <div style={{ flex: 1, height: '8px', background: '#EBF0F8', borderRadius: '4px', overflow: 'hidden' }}>
                    <div style={{ height: '100%', width: `${v}%`, background: c, borderRadius: '4px' }} />
                  </div>
                  <div style={{ fontSize: '11px', color: 'var(--navy)', fontFamily: "'DM Mono',monospace", width: '48px', textAlign: 'right' }}>{val}</div>
                </div>
              ))}
            </div>
          </div>

          {/* Diversification */}
          <div style={{ background: 'var(--white)', borderRadius: '12px', padding: '24px', boxShadow: '0 2px 12px rgba(0,0,0,0.06)' }}>
            <h4 style={{ fontSize: '13px', fontWeight: 600, color: 'var(--navy)', marginBottom: '16px' }}>Diversification Score</h4>
            <div style={{ display: 'flex', alignItems: 'center', gap: '20px' }}>
              <div style={{ textAlign: 'center' }}>
                <div style={{ fontFamily: "'Playfair Display',serif", fontSize: '48px', color: 'var(--teal)', fontWeight: 700, lineHeight: 1 }}>50</div>
                <div style={{ fontSize: '11px', color: 'var(--gray)', marginTop: '4px' }}>out of 100</div>
              </div>
              <div style={{ flex: 1 }}>
                <div style={{ height: '12px', background: '#EBF0F8', borderRadius: '6px', overflow: 'hidden', marginBottom: '8px' }}>
                  <div style={{ height: '100%', width: '50%', background: 'linear-gradient(90deg,var(--teal),var(--teal2))', borderRadius: '6px' }} />
                </div>
                <p style={{ fontSize: '11px', color: 'var(--gray)', lineHeight: 1.5 }}>
                  2 metros · 2 assets. Score above 75 requires 4+ distinct metropolitan markets.
                </p>
              </div>
            </div>
          </div>
        </div>
      </div>

    </section>
  )
}
