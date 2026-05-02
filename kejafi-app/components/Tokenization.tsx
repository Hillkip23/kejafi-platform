interface TokenizeProps {
  onOpenModal: () => void
}

const tokens = [
  {
    tag: 'FINE5', name: 'Charlotte Multifamily', location: 'Charlotte, NC · Cap Rate 5.5%',
    price: '$6.85', value: '$685,000', noi: '$47,808', supply: '100,000', mcap: '$685K', irr: 12.3, irrPct: 72
  },
  {
    tag: 'FINE6', name: 'Austin Multifamily', location: 'Austin, TX · Cap Rate 5.2%',
    price: '$12.50', value: '$1,250,000', noi: '$78,000', supply: '100,000', mcap: '$1.25M', irr: 14.1, irrPct: 83
  }
]

export default function Tokenization({ onOpenModal }: TokenizeProps) {
  return (
    <section id="tokenize" style={{ padding: '96px 48px', background: 'var(--navy)' }}>
      <div style={{ marginBottom: '56px' }}>
        <div style={{ fontSize: '11px', color: 'var(--teal)', fontFamily: "'DM Mono',monospace", letterSpacing: '2px', textTransform: 'uppercase', marginBottom: '16px' }}>Stage 2</div>
        <h2 style={{ fontFamily: "'Playfair Display',serif", fontSize: 'clamp(32px,5vw,48px)', fontWeight: 700, marginBottom: '12px' }}>Tokenized Properties</h2>
        <p style={{ fontSize: '16px', color: 'rgba(255,255,255,0.55)', maxWidth: '560px', lineHeight: 1.7, fontWeight: 300 }}>
          Live ERC-20 tokens backed by real property valuations. Each token represents fractional ownership with transparent on-chain economics.
        </p>
      </div>

      <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '24px', marginBottom: '24px' }}>
        {tokens.map(t => (
          <div key={t.tag} style={{
            background: 'rgba(255,255,255,0.04)', border: '1px solid rgba(0,180,204,0.2)',
            borderRadius: '16px', padding: '32px', position: 'relative',
            transition: 'all 0.3s', overflow: 'hidden'
          }}
            onMouseEnter={e => { (e.currentTarget as HTMLElement).style.borderColor = 'rgba(0,180,204,0.5)'; (e.currentTarget as HTMLElement).style.transform = 'translateY(-4px)' }}
            onMouseLeave={e => { (e.currentTarget as HTMLElement).style.borderColor = 'rgba(0,180,204,0.2)'; (e.currentTarget as HTMLElement).style.transform = 'translateY(0)' }}
          >
            <div style={{ position: 'absolute', top: 0, left: 0, right: 0, height: '2px', background: 'linear-gradient(90deg, var(--teal), var(--teal2))' }} />

            <div style={{ display: 'inline-block', padding: '4px 10px', borderRadius: '4px', background: 'rgba(0,180,204,0.12)', color: 'var(--teal)', fontSize: '10px', fontFamily: "'DM Mono',monospace", letterSpacing: '1px', marginBottom: '16px' }}>{t.tag}</div>
            <h3 style={{ fontFamily: "'Playfair Display',serif", fontSize: '26px', marginBottom: '4px' }}>{t.name}</h3>
            <p style={{ fontSize: '13px', color: 'var(--gray)', marginBottom: '24px' }}>📍 {t.location}</p>

            <div style={{ display: 'flex', alignItems: 'baseline', gap: '8px', marginBottom: '24px' }}>
              <span style={{ fontFamily: "'Playfair Display',serif", fontSize: '40px', color: 'var(--teal)' }}>{t.price}</span>
              <span style={{ fontSize: '13px', color: 'var(--gray)' }}>per token</span>
            </div>

            <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '10px', marginBottom: '20px' }}>
              {[
                { l: 'Property Value', v: t.value, c: 'var(--teal)' },
                { l: 'Annual NOI', v: t.noi, c: 'var(--white)' },
                { l: 'Total Supply', v: t.supply, c: 'var(--white)' },
                { l: 'Market Cap', v: t.mcap, c: 'var(--teal)' },
              ].map(({ l, v, c }) => (
                <div key={l} style={{ background: 'rgba(255,255,255,0.03)', borderRadius: '8px', padding: '14px' }}>
                  <div style={{ fontSize: '10px', color: 'var(--gray)', textTransform: 'uppercase', letterSpacing: '1px', marginBottom: '4px' }}>{l}</div>
                  <div style={{ fontSize: '15px', fontWeight: 600, color: c, fontFamily: "'DM Mono',monospace" }}>{v}</div>
                </div>
              ))}
            </div>

            <div style={{ marginBottom: '20px' }}>
              <div style={{ display: 'flex', justifyContent: 'space-between', fontSize: '11px', color: 'var(--gray)', marginBottom: '6px' }}>
                <span>Projected 5-Year IRR</span>
                <span style={{ color: 'var(--green)', fontWeight: 700 }}>{t.irr}%</span>
              </div>
              <div style={{ height: '8px', background: 'rgba(255,255,255,0.06)', borderRadius: '4px', overflow: 'hidden' }}>
                <div style={{ height: '100%', width: `${t.irrPct}%`, background: 'linear-gradient(90deg, var(--teal), var(--green))', borderRadius: '4px' }} />
              </div>
            </div>

            <button
              onClick={onOpenModal}
              style={{
                width: '100%', padding: '13px', borderRadius: '8px',
                background: 'var(--teal)', color: 'var(--navy)',
                fontSize: '13px', fontWeight: 700, border: 'none',
                cursor: 'pointer', transition: 'all 0.2s'
              }}
              onMouseEnter={e => (e.currentTarget.style.background = 'var(--teal2)')}
              onMouseLeave={e => (e.currentTarget.style.background = 'var(--teal)')}
            >
              Invest in {t.tag} →
            </button>
          </div>
        ))}
      </div>

      {/* Contract addresses */}
      <div style={{
        background: 'rgba(0,180,204,0.05)', border: '1px solid rgba(0,180,204,0.2)',
        borderRadius: '16px', padding: '28px 32px'
      }}>
        <div style={{ fontSize: '11px', color: 'var(--teal)', fontFamily: "'DM Mono',monospace", letterSpacing: '1px', marginBottom: '20px' }}>
          SMART CONTRACT DEPLOYMENT — SEPOLIA TESTNET
        </div>
        <div style={{ display: 'grid', gridTemplateColumns: 'repeat(3,1fr)', gap: '20px' }}>
          {[
            { l: 'UNISWAP V3 POOL', a: '0x0Bf78f76c86153E433dAA5Ac6A88453D30968e27' },
            { l: 'FINE5 TOKEN CONTRACT', a: '0x0FB987BEE67FD839cb1158B0712d5e4Be483dd2E' },
            { l: 'FINE6 TOKEN CONTRACT', a: '0xe051C1eA47b246c79f3bac4e58E459cF2Aa20692' },
          ].map(({ l, a }) => (
            <div key={l}>
              <div style={{ fontSize: '10px', color: 'var(--gray)', letterSpacing: '1px', marginBottom: '6px' }}>{l}</div>
              <div style={{ fontSize: '11px', color: 'var(--teal)', fontFamily: "'DM Mono',monospace", wordBreak: 'break-all' }}>{a}</div>
            </div>
          ))}
        </div>
        <div style={{
          display: 'inline-flex', alignItems: 'center', gap: '6px',
          padding: '4px 12px', borderRadius: '20px',
          background: 'rgba(0,180,204,0.12)', border: '1px solid rgba(0,180,204,0.2)',
          fontSize: '10px', color: 'var(--teal)', fontFamily: "'DM Mono',monospace",
          letterSpacing: '1px', marginTop: '16px'
        }}>
          <span style={{ width: '6px', height: '6px', borderRadius: '50%', background: 'var(--green)', animation: 'pulse 2s infinite' }} />
          Sepolia Testnet · Chain ID 11155111 · Gas cost ~$145
        </div>
      </div>

    </section>
  )
}
