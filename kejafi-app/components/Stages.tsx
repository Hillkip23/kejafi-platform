const stages = [
  {
    num: '01', icon: '📊', title: 'Metro Risk Analysis', color: '#0D1B3E',
    desc: 'Stochastic rent forecasting using Ornstein-Uhlenbeck processes with population growth and supply elasticity adjustments.',
    features: ['OU Process + Jump-Diffusion', 'Population Growth Integration', 'Supply Elasticity Adjustment', 'Kejafi Risk Score (0–100)', 'Multi-metro Comparison'],
    target: 'metro'
  },
  {
    num: '02', icon: '🔗', title: 'Property Tokenization', color: '#028090',
    desc: 'NOI-based direct capitalisation valuation with live ERC-20 deployment and Uniswap V3 AMM liquidity provision.',
    features: ['NOI Valuation Model', '5-Year IRR Projection', 'ERC-20 Token Deployment', 'Uniswap V3 AMM Liquidity', 'Sepolia Testnet Live'],
    target: 'tokenize'
  },
  {
    num: '03', icon: '📈', title: 'Portfolio Management', color: '#2C3E50',
    desc: 'Institutional-grade analytics with Monte Carlo simulation, VaR measurement, and proprietary diversification scoring.',
    features: ['Monte Carlo (10,000 scenarios)', 'Value at Risk (95% VaR)', 'Sharpe Ratio Analysis', 'Diversification Score', 'Geographic Allocation'],
    target: 'portfolio'
  }
]

export default function Stages() {
  const scrollTo = (id: string) => document.getElementById(id)?.scrollIntoView({ behavior: 'smooth' })

  return (
    <section id="stages" style={{ padding: '96px 48px', background: 'var(--navy)' }}>
      <div style={{ textAlign: 'center', marginBottom: '72px' }}>
        <div style={{ fontSize: '11px', color: 'var(--teal)', fontFamily: "'DM Mono',monospace", letterSpacing: '2px', textTransform: 'uppercase', marginBottom: '16px' }}>
          The Platform
        </div>
        <h2 style={{ fontFamily: "'Playfair Display',serif", fontSize: 'clamp(32px,5vw,52px)', fontWeight: 700, lineHeight: 1.1, marginBottom: '16px' }}>
          Three Integrated Stages
        </h2>
        <p style={{ fontSize: '16px', color: 'rgba(255,255,255,0.55)', maxWidth: '560px', margin: '0 auto', lineHeight: 1.7, fontWeight: 300 }}>
          Each stage feeds directly into the next — metro risk outputs calibrate token pricing, tokenized assets form the portfolio universe.
        </p>
      </div>

      <div style={{ display: 'grid', gridTemplateColumns: 'repeat(3,1fr)', gap: '2px', borderRadius: '16px', overflow: 'hidden' }}>
        {stages.map(({ num, icon, title, color, desc, features, target }) => (
          <div
            key={num}
            onClick={() => scrollTo(target)}
            style={{
              background: 'rgba(22,35,71,0.8)', padding: '48px 36px',
              cursor: 'pointer', transition: 'all 0.3s',
              borderTop: `3px solid ${color === '#028090' ? 'var(--teal)' : 'transparent'}`
            }}
            onMouseEnter={e => {
              (e.currentTarget as HTMLElement).style.background = 'rgba(0,180,204,0.08)'
              ;(e.currentTarget as HTMLElement).style.borderTopColor = 'var(--teal)'
            }}
            onMouseLeave={e => {
              (e.currentTarget as HTMLElement).style.background = 'rgba(22,35,71,0.8)'
              ;(e.currentTarget as HTMLElement).style.borderTopColor = color === '#028090' ? 'var(--teal)' : 'transparent'
            }}
          >
            <div style={{ fontSize: '11px', color: 'var(--teal)', fontFamily: "'DM Mono',monospace", letterSpacing: '2px', marginBottom: '20px' }}>
              STAGE {num}
            </div>
            <div style={{
              width: '52px', height: '52px', borderRadius: '12px',
              background: 'rgba(0,180,204,0.1)', border: '1px solid rgba(0,180,204,0.15)',
              display: 'flex', alignItems: 'center', justifyContent: 'center',
              fontSize: '22px', marginBottom: '24px'
            }}>
              {icon}
            </div>
            <h3 style={{ fontFamily: "'Playfair Display',serif", fontSize: '22px', fontWeight: 700, marginBottom: '12px' }}>
              {title}
            </h3>
            <p style={{ fontSize: '13px', color: 'var(--gray)', lineHeight: 1.7, marginBottom: '24px' }}>{desc}</p>
            <ul style={{ listStyle: 'none' }}>
              {features.map(f => (
                <li key={f} style={{
                  fontSize: '12px', color: 'rgba(255,255,255,0.6)',
                  padding: '5px 0', borderBottom: '1px solid rgba(255,255,255,0.04)',
                  display: 'flex', alignItems: 'center', gap: '8px'
                }}>
                  <span style={{ color: 'var(--teal)', fontSize: '9px' }}>▸</span>
                  {f}
                </li>
              ))}
            </ul>
          </div>
        ))}
      </div>

    </section>
  )
}
