import { useState } from 'react'

export function Waitlist() {
  const [email, setEmail] = useState('')
  const [submitted, setSubmitted] = useState(false)
  const [error, setError] = useState('')

  const handleSubmit = () => {
    if (!email || !email.includes('@')) { setError('Please enter a valid email'); return }
    setSubmitted(true)
    setError('')
  }

  return (
    <section id="waitlist" style={{
      padding: '96px 48px', textAlign: 'center',
      background: 'linear-gradient(135deg, var(--navy2) 0%, var(--navy) 100%)',
      position: 'relative', overflow: 'hidden'
    }}>
      <div style={{
        position: 'absolute', inset: 0,
        background: 'radial-gradient(ellipse 80% 60% at 50% 50%, rgba(0,180,204,0.07) 0%, transparent 70%)'
      }} />
      <div style={{ position: 'relative', zIndex: 2, maxWidth: '560px', margin: '0 auto' }}>
        <div style={{ fontSize: '11px', color: 'var(--teal)', fontFamily: "'DM Mono',monospace", letterSpacing: '2px', textTransform: 'uppercase', marginBottom: '16px' }}>Early Access</div>
        <h2 style={{ fontFamily: "'Playfair Display',serif", fontSize: 'clamp(32px,5vw,48px)', fontWeight: 700, marginBottom: '16px' }}>Join the Kejafi Waitlist</h2>
        <p style={{ fontSize: '16px', color: 'rgba(255,255,255,0.55)', lineHeight: 1.7, fontWeight: 300, marginBottom: '36px' }}>
          Be first to access tokenized real estate analytics when Kejafi launches on mainnet. No spam — just platform updates.
        </p>

        {!submitted ? (
          <>
            <div style={{ display: 'flex', gap: '12px', maxWidth: '440px', margin: '0 auto' }}>
              <input
                type="email"
                value={email}
                onChange={e => setEmail(e.target.value)}
                placeholder="your@email.com"
                onKeyDown={e => e.key === 'Enter' && handleSubmit()}
                style={{
                  flex: 1, padding: '14px 18px', borderRadius: '8px',
                  background: 'rgba(255,255,255,0.06)',
                  border: `1px solid ${error ? 'var(--red)' : 'rgba(0,180,204,0.2)'}`,
                  color: 'var(--white)', fontSize: '14px', outline: 'none',
                  fontFamily: "'DM Sans', sans-serif"
                }}
              />
              <button
                onClick={handleSubmit}
                style={{
                  padding: '14px 24px', background: 'var(--teal)',
                  color: 'var(--navy)', borderRadius: '8px',
                  fontSize: '14px', fontWeight: 700, border: 'none',
                  cursor: 'pointer', whiteSpace: 'nowrap', transition: 'all 0.2s'
                }}
                onMouseEnter={e => (e.currentTarget.style.background = 'var(--teal2)')}
                onMouseLeave={e => (e.currentTarget.style.background = 'var(--teal)')}
              >
                Join Now
              </button>
            </div>
            {error && <p style={{ color: 'var(--red)', fontSize: '12px', marginTop: '8px' }}>{error}</p>}
          </>
        ) : (
          <div style={{
            padding: '16px 24px',
            background: 'rgba(29,191,115,0.1)', border: '1px solid rgba(29,191,115,0.3)',
            borderRadius: '8px', color: 'var(--green)', fontSize: '14px', maxWidth: '440px', margin: '0 auto'
          }}>
            ✓ You&apos;re on the list! We&apos;ll be in touch when Kejafi launches.
          </div>
        )}

        <p style={{ fontSize: '12px', color: 'var(--gray)', marginTop: '14px' }}>
          Currently in testnet. Mainnet launch 2026. All tokens are for demonstration only.
        </p>

        <div style={{ display: 'flex', justifyContent: 'center', gap: '32px', marginTop: '48px', flexWrap: 'wrap' }}>
          {['✓ Live on Sepolia', '✓ Open Source GitHub', '✓ Peer-Reviewed Model', '✓ UNC Charlotte Research'].map(t => (
            <div key={t} style={{ fontSize: '12px', color: 'var(--gray)' }}>{t}</div>
          ))}
        </div>
      </div>
    </section>
  )
}

export function Footer() {
  const navTo = (id: string) => document.getElementById(id)?.scrollIntoView({ behavior: 'smooth' })

  return (
    <footer style={{
      background: 'var(--navy2)', padding: '40px 48px',
      borderTop: '1px solid rgba(0,180,204,0.12)',
      display: 'flex', alignItems: 'center', justifyContent: 'space-between',
      flexWrap: 'wrap', gap: '16px'
    }}>
      <div style={{ fontFamily: "'Playfair Display',serif", fontSize: '18px', fontWeight: 900, color: 'var(--teal)' }}>KEJAFI</div>
      <div style={{ display: 'flex', gap: '24px', flexWrap: 'wrap' }}>
        {[
          { l: 'GitHub', href: 'https://github.com/Hillkip23/kejafi-platform' },
          { l: 'Live Demo', href: 'https://kejafi-stage2.streamlit.app' },
          { l: 'API Docs', href: 'https://kejafi-platform.onrender.com/docs' },
          { l: 'Waitlist', onClick: () => navTo('waitlist') },
        ].map(({ l, href, onClick }) => (
          href ? (
            <a key={l} href={href} target="_blank" rel="noopener noreferrer"
              style={{ fontSize: '12px', color: 'var(--gray)', transition: 'color 0.2s', cursor: 'pointer' }}
              onMouseEnter={e => (e.currentTarget.style.color = 'var(--white)')}
              onMouseLeave={e => (e.currentTarget.style.color = 'var(--gray)')}
            >{l}</a>
          ) : (
            <button key={l} onClick={onClick}
              style={{ fontSize: '12px', color: 'var(--gray)', background: 'none', border: 'none', cursor: 'pointer', padding: 0, transition: 'color 0.2s' }}
              onMouseEnter={e => (e.currentTarget.style.color = 'var(--white)')}
              onMouseLeave={e => (e.currentTarget.style.color = 'var(--gray)')}
            >{l}</button>
          )
        ))}
      </div>
      <div style={{ fontSize: '11px', color: 'var(--gray)' }}>© 2026 Kejafi · Hillary Cheruiyot · Built at UNC Charlotte</div>
    </footer>
  )
}
