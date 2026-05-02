interface HeroProps {
  onOpenModal: () => void
}

export default function Hero({ onOpenModal }: HeroProps) {
  const scrollTo = (id: string) => document.getElementById(id)?.scrollIntoView({ behavior: 'smooth' })

  return (
    <section id="home" style={{
      minHeight: '100vh', display: 'flex', alignItems: 'center',
      padding: '100px 48px 60px', position: 'relative', overflow: 'hidden'
    }}>
      {/* Background effects */}
      <div style={{
        position: 'absolute', inset: 0,
        background: `
          radial-gradient(ellipse 80% 60% at 60% 40%, rgba(0,180,204,0.08) 0%, transparent 60%),
          radial-gradient(ellipse 50% 80% at 90% 80%, rgba(0,212,176,0.05) 0%, transparent 50%)
        `
      }} />
      <div style={{
        position: 'absolute', inset: 0,
        backgroundImage: 'linear-gradient(rgba(0,180,204,0.04) 1px,transparent 1px), linear-gradient(90deg,rgba(0,180,204,0.04) 1px,transparent 1px)',
        backgroundSize: '64px 64px'
      }} />

      {/* Content */}
      <div style={{ position: 'relative', zIndex: 2, maxWidth: '680px' }}>
        <div style={{
          display: 'inline-flex', alignItems: 'center', gap: '8px',
          padding: '6px 14px', borderRadius: '20px',
          border: '1px solid rgba(0,180,204,0.3)',
          background: 'rgba(0,180,204,0.08)',
          fontSize: '11px', fontWeight: 600, color: 'var(--teal)',
          letterSpacing: '1.5px', textTransform: 'uppercase',
          marginBottom: '28px'
        }}>
          <span style={{
            width: '6px', height: '6px', borderRadius: '50%',
            background: 'var(--teal)',
            animation: 'pulse 2s infinite'
          }} />
          Live on Sepolia Testnet
        </div>

        <h1 style={{
          fontFamily: "'Playfair Display', serif",
          fontSize: 'clamp(52px, 8vw, 90px)',
          fontWeight: 900, lineHeight: 1.0,
          letterSpacing: '-2px', marginBottom: '24px'
        }}>
          Real Estate.<br />
          <span style={{
            background: 'linear-gradient(135deg, var(--teal), var(--teal2))',
            WebkitBackgroundClip: 'text', WebkitTextFillColor: 'transparent',
            backgroundClip: 'text'
          }}>Tokenized.</span><br />
          Quantified.
        </h1>

        <p style={{
          fontSize: '18px', color: 'rgba(255,255,255,0.6)',
          lineHeight: 1.7, marginBottom: '40px',
          maxWidth: '520px', fontWeight: 300
        }}>
          Kejafi bridges institutional-grade stochastic risk modelling with live DeFi 
          infrastructure — from metro rent forecasting to on-chain fractional ownership.
        </p>

        <div style={{ display: 'flex', gap: '14px', flexWrap: 'wrap' }}>
          <button
            onClick={() => scrollTo('stages')}
            style={{
              padding: '14px 28px', background: 'var(--teal)',
              color: 'var(--navy)', borderRadius: '8px',
              fontSize: '14px', fontWeight: 700, border: 'none',
              transition: 'all 0.2s'
            }}
          >
            Explore Platform
          </button>
          <button
            onClick={onOpenModal}
            style={{
              padding: '14px 28px', background: 'transparent',
              color: 'var(--white)', borderRadius: '8px',
              fontSize: '14px', fontWeight: 500,
              border: '1px solid rgba(255,255,255,0.2)',
              transition: 'all 0.2s'
            }}
          >
            Request Access →
          </button>
        </div>

        {/* Stats row */}
        <div style={{
          display: 'flex', gap: '40px', marginTop: '56px',
          paddingTop: '40px',
          borderTop: '1px solid rgba(0,180,204,0.15)',
          flexWrap: 'wrap'
        }}>
          {[
            { num: '$280T', lbl: 'Global RE Market' },
            { num: '12–14%', lbl: 'Projected IRR' },
            { num: '0.77', lbl: 'Sharpe Ratio' },
            { num: '32%', lbl: 'VaR Reduction' },
          ].map(({ num, lbl }) => (
            <div key={lbl}>
              <div style={{
                fontFamily: "'Playfair Display', serif",
                fontSize: '30px', fontWeight: 700
              }}>{num}</div>
              <div style={{ fontSize: '12px', color: 'var(--gray)', marginTop: '4px' }}>{lbl}</div>
            </div>
          ))}
        </div>
      </div>

      {/* Right side cards */}
      <div style={{
        position: 'absolute', right: '48px', top: '50%',
        transform: 'translateY(-50%)',
        width: '420px', zIndex: 2,
        display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '14px'
      }} className="hero-cards">
        {[
          { label: 'AUSTIN RISK SCORE', val: '59/100', sub: 'Pop. growth 13.9%', pct: 59, color: 'var(--teal)' },
          { label: 'FINE6 IRR', val: '14.1%', sub: '5-year projection', pct: 82, color: 'var(--green)' },
        ].map(({ label, val, sub, pct, color }) => (
          <div key={label} style={{
            background: 'rgba(255,255,255,0.04)',
            border: '1px solid rgba(0,180,204,0.15)',
            borderRadius: '12px', padding: '20px',
            backdropFilter: 'blur(10px)'
          }}>
            <div style={{ fontSize: '10px', color: 'var(--teal)', fontFamily: "'DM Mono',monospace", letterSpacing: '1px', marginBottom: '8px' }}>{label}</div>
            <div style={{ fontFamily: "'Playfair Display',serif", fontSize: '28px', color: 'var(--white)' }}>{val}</div>
            <div style={{ fontSize: '11px', color: 'var(--gray)', marginTop: '4px' }}>{sub}</div>
            <div style={{ height: '4px', background: 'rgba(255,255,255,0.08)', borderRadius: '2px', marginTop: '12px', overflow: 'hidden' }}>
              <div style={{ height: '100%', width: `${pct}%`, background: `linear-gradient(90deg, var(--teal), ${color})`, borderRadius: '2px' }} />
            </div>
          </div>
        ))}
        <div style={{
          gridColumn: '1/-1',
          background: 'rgba(255,255,255,0.04)',
          border: '1px solid rgba(0,180,204,0.15)',
          borderRadius: '12px', padding: '20px',
          backdropFilter: 'blur(10px)'
        }}>
          <div style={{ fontSize: '10px', color: 'var(--teal)', fontFamily: "'DM Mono',monospace", letterSpacing: '1px', marginBottom: '12px' }}>
            PORTFOLIO ANALYTICS (10,000 MC SCENARIOS)
          </div>
          <div style={{ display: 'flex', gap: '24px' }}>
            {[
              { v: '11.2%', l: 'Expected Return', c: 'var(--green)' },
              { v: '0.77', l: 'Sharpe Ratio', c: 'var(--white)' },
              { v: '−12.8%', l: 'VaR 95%', c: 'var(--red)' },
              { v: '50/100', l: 'Div. Score', c: 'var(--teal)' },
            ].map(({ v, l, c }) => (
              <div key={l}>
                <div style={{ fontFamily: "'Playfair Display',serif", fontSize: '20px', color: c }}>{v}</div>
                <div style={{ fontSize: '10px', color: 'var(--gray)', marginTop: '2px' }}>{l}</div>
              </div>
            ))}
          </div>
        </div>
      </div>

    </section>
  )
}
