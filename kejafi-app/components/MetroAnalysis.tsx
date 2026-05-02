import { useState } from 'react'

const metros = {
  charlotte: {
    name: 'Charlotte, NC', score: '50/100', scoreColor: '#F5A623',
    scoreLabel: 'Moderate Risk Profile',
    pop: '10.2%', elast: '0.35', vol: '8.5%', rg: '+1.6%',
    kappa: '0.42', theta: '$1,847/mo', sigma: '0.085', lambda: '0.08/yr',
    bars: [{ l: 'Pop. Growth', v: 65, val: '10.2%', c: '#00B4CC' }, { l: 'Elasticity', v: 58, val: '0.35', c: '#00D4B0' }, { l: 'Volatility', v: 42, val: '8.5%', c: '#F5A623' }, { l: 'Risk Score', v: 50, val: '50/100', c: '#1DBF73' }]
  },
  austin: {
    name: 'Austin, TX', score: '59/100', scoreColor: '#1DBF73',
    scoreLabel: 'Strong Growth Profile',
    pop: '13.9%', elast: '0.48', vol: '12.1%', rg: '−3.0%',
    kappa: '0.38', theta: '$2,210/mo', sigma: '0.121', lambda: '0.12/yr',
    bars: [{ l: 'Pop. Growth', v: 89, val: '13.9%', c: '#00B4CC' }, { l: 'Elasticity', v: 80, val: '0.48', c: '#00D4B0' }, { l: 'Volatility', v: 60, val: '12.1%', c: '#F5A623' }, { l: 'Risk Score', v: 59, val: '59/100', c: '#1DBF73' }]
  },
  sf: {
    name: 'San Francisco, CA', score: '35/100', scoreColor: '#FF5A5F',
    scoreLabel: 'High Volatility — Inelastic',
    pop: '2.8%', elast: '0.08', vol: '15.2%', rg: '—',
    kappa: '0.61', theta: '$3,840/mo', sigma: '0.152', lambda: '0.22/yr',
    bars: [{ l: 'Pop. Growth', v: 18, val: '2.8%', c: '#FF5A5F' }, { l: 'Elasticity', v: 8, val: '0.08', c: '#FF5A5F' }, { l: 'Volatility', v: 76, val: '15.2%', c: '#FF5A5F' }, { l: 'Risk Score', v: 35, val: '35/100', c: '#FF5A5F' }]
  }
}

type MetroKey = keyof typeof metros

export default function MetroAnalysis() {
  const [selected, setSelected] = useState<MetroKey>('charlotte')
  const m = metros[selected]

  return (
    <section id="metro" style={{ padding: '96px 48px', background: 'var(--off)', color: 'var(--navy)' }}>
      <div style={{ marginBottom: '48px' }}>
        <div style={{ fontSize: '11px', color: 'var(--teal)', fontFamily: "'DM Mono',monospace", letterSpacing: '2px', textTransform: 'uppercase', marginBottom: '16px' }}>Stage 1</div>
        <h2 style={{ fontFamily: "'Playfair Display',serif", fontSize: 'clamp(32px,5vw,48px)', fontWeight: 700, color: 'var(--navy)', marginBottom: '12px' }}>Metro Risk Analysis</h2>
        <p style={{ fontSize: '16px', color: 'var(--gray)', maxWidth: '560px', lineHeight: 1.7, fontWeight: 300 }}>
          Select a metropolitan market to view Ornstein-Uhlenbeck model parameters, risk scores, and rent dynamics.
        </p>
      </div>

      {/* Metro selector */}
      <div style={{ display: 'flex', gap: '8px', marginBottom: '32px', flexWrap: 'wrap' }}>
        {(Object.keys(metros) as MetroKey[]).map(key => (
          <button
            key={key}
            onClick={() => setSelected(key)}
            style={{
              padding: '9px 20px', borderRadius: '6px', fontSize: '13px', fontWeight: 600,
              cursor: 'pointer', transition: 'all 0.2s',
              background: selected === key ? 'var(--navy)' : 'transparent',
              color: selected === key ? 'var(--white)' : 'var(--gray)',
              border: `1px solid ${selected === key ? 'var(--navy)' : '#ddd'}`
            }}
          >
            {metros[key].name}
          </button>
        ))}
      </div>

      <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '32px' }}>
        {/* Left: metro card */}
        <div>
          <div style={{ background: 'var(--white)', borderRadius: '16px', padding: '32px', boxShadow: '0 4px 24px rgba(0,0,0,0.08)' }}>
            <h3 style={{ fontFamily: "'Playfair Display',serif", fontSize: '24px', color: 'var(--navy)', marginBottom: '8px' }}>{m.name}</h3>
            <div style={{ display: 'flex', alignItems: 'center', gap: '10px', marginBottom: '24px' }}>
              <span style={{ padding: '4px 12px', borderRadius: '20px', fontSize: '12px', fontWeight: 700, fontFamily: "'DM Mono',monospace", background: `${m.scoreColor}20`, color: m.scoreColor }}>{m.score}</span>
              <span style={{ fontSize: '12px', color: 'var(--gray)' }}>{m.scoreLabel}</span>
            </div>

            <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '12px', marginBottom: '24px' }}>
              {[
                { label: 'Pop. Growth (5yr)', val: m.pop }, { label: 'Supply Elasticity', val: m.elast },
                { label: 'Rent Volatility', val: m.vol }, { label: 'Rent Growth', val: m.rg }
              ].map(({ label, val }) => (
                <div key={label} style={{ background: 'var(--off)', borderRadius: '10px', padding: '16px' }}>
                  <div style={{ fontSize: '10px', color: 'var(--gray)', textTransform: 'uppercase', letterSpacing: '1px', marginBottom: '6px' }}>{label}</div>
                  <div style={{ fontFamily: "'Playfair Display',serif", fontSize: '24px', color: 'var(--navy)' }}>{val}</div>
                </div>
              ))}
            </div>

            <div style={{ background: 'var(--navy)', borderRadius: '10px', padding: '20px' }}>
              <div style={{ fontSize: '11px', color: 'var(--teal)', fontFamily: "'DM Mono',monospace", letterSpacing: '1px', marginBottom: '14px' }}>OU MODEL PARAMETERS</div>
              {[
                { name: 'κ (mean reversion)', val: m.kappa }, { name: 'θ_adj (equilibrium)', val: m.theta },
                { name: 'σ_adj (volatility)', val: m.sigma }, { name: 'Jump intensity λ', val: m.lambda }
              ].map(({ name, val }) => (
                <div key={name} style={{ display: 'flex', justifyContent: 'space-between', padding: '7px 0', borderBottom: '1px solid rgba(255,255,255,0.06)' }}>
                  <span style={{ fontSize: '12px', color: 'rgba(255,255,255,0.5)', fontFamily: "'DM Mono',monospace" }}>{name}</span>
                  <span style={{ fontSize: '12px', color: 'var(--teal)', fontFamily: "'DM Mono',monospace", fontWeight: 500 }}>{val}</span>
                </div>
              ))}
            </div>
          </div>
        </div>

        {/* Right: comparison chart */}
        <div>
          <div style={{ background: 'var(--white)', borderRadius: '16px', padding: '28px', boxShadow: '0 4px 24px rgba(0,0,0,0.08)', marginBottom: '20px' }}>
            <h3 style={{ fontFamily: "'Playfair Display',serif", fontSize: '18px', color: 'var(--navy)', marginBottom: '20px' }}>Selected Metro — Risk Metrics</h3>
            <div style={{ display: 'flex', flexDirection: 'column', gap: '12px' }}>
              {m.bars.map(({ l, v, val, c }) => (
                <div key={l} style={{ display: 'flex', alignItems: 'center', gap: '12px' }}>
                  <div style={{ fontSize: '12px', color: 'var(--gray)', width: '100px', flexShrink: 0, textAlign: 'right' }}>{l}</div>
                  <div style={{ flex: 1, height: '10px', background: '#EBF0F8', borderRadius: '5px', overflow: 'hidden' }}>
                    <div style={{ height: '100%', width: `${v}%`, background: c, borderRadius: '5px', transition: 'width 0.8s ease' }} />
                  </div>
                  <div style={{ fontSize: '11px', color: 'var(--navy)', fontFamily: "'DM Mono',monospace", width: '55px' }}>{val}</div>
                </div>
              ))}
            </div>
          </div>

          <div style={{ background: 'var(--navy)', borderRadius: '12px', padding: '20px 24px', display: 'flex', alignItems: 'flex-start', gap: '14px' }}>
            <span style={{ fontSize: '18px' }}>💡</span>
            <p style={{ fontSize: '13px', color: 'rgba(202,220,252,0.9)', lineHeight: 1.6 }}>
              <strong style={{ color: 'var(--teal)' }}>R² = 0.73</strong> — Population growth explains 73% of long-run rent variation across US metros (p &lt; 0.01). Inelastic markets (ε &lt; 0.15) exhibit <strong style={{ color: 'var(--teal)' }}>40–50% higher volatility</strong>.
            </p>
          </div>
        </div>
      </div>

    </section>
  )
}
