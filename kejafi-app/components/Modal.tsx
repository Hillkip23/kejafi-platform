import { useState } from 'react'

interface ModalProps {
  isOpen: boolean
  onClose: () => void
}

export default function Modal({ isOpen, onClose }: ModalProps) {
  const [submitted, setSubmitted] = useState(false)
  const [name, setName] = useState('')
  const [email, setEmail] = useState('')
  const [type, setType] = useState('Retail Investor')
  const [interest, setInterest] = useState('FINE5 — Charlotte ($6.85/token)')

  if (!isOpen) return null

  return (
    <div
      onClick={e => { if (e.target === e.currentTarget) onClose() }}
      style={{
        position: 'fixed', inset: 0, zIndex: 2000,
        background: 'rgba(13,27,62,0.92)', backdropFilter: 'blur(8px)',
        display: 'flex', alignItems: 'center', justifyContent: 'center',
        padding: '20px'
      }}
    >
      <div style={{
        background: 'var(--navy2)', border: '1px solid rgba(0,180,204,0.2)',
        borderRadius: '20px', padding: '40px', maxWidth: '480px', width: '100%',
        position: 'relative'
      }}>
        <button
          onClick={onClose}
          style={{
            position: 'absolute', top: '16px', right: '16px',
            width: '32px', height: '32px', borderRadius: '50%',
            background: 'rgba(255,255,255,0.06)', border: 'none',
            color: 'var(--gray)', fontSize: '18px', cursor: 'pointer',
            display: 'flex', alignItems: 'center', justifyContent: 'center',
            transition: 'all 0.2s'
          }}
          onMouseEnter={e => { (e.currentTarget.style.background = 'rgba(255,255,255,0.12)'); (e.currentTarget.style.color = 'var(--white)') }}
          onMouseLeave={e => { (e.currentTarget.style.background = 'rgba(255,255,255,0.06)'); (e.currentTarget.style.color = 'var(--gray)') }}
        >
          ×
        </button>

        {!submitted ? (
          <>
            <h3 style={{ fontFamily: "'Playfair Display',serif", fontSize: '28px', marginBottom: '8px' }}>Request Early Access</h3>
            <p style={{ fontSize: '13px', color: 'var(--gray)', marginBottom: '28px', lineHeight: 1.6 }}>
              Kejafi is currently in testnet. Join the waitlist for mainnet launch access, institutional demos, and research updates.
            </p>

            {[
              { label: 'FULL NAME', type: 'text', value: name, onChange: setName, placeholder: 'Your name' },
              { label: 'EMAIL ADDRESS', type: 'email', value: email, onChange: setEmail, placeholder: 'your@email.com' },
            ].map(({ label, type: t, value, onChange, placeholder }) => (
              <div key={label} style={{ marginBottom: '14px' }}>
                <label style={{ fontSize: '11px', color: 'var(--gray)', display: 'block', marginBottom: '6px', letterSpacing: '0.5px' }}>{label}</label>
                <input
                  type={t} value={value}
                  onChange={e => onChange(e.target.value)}
                  placeholder={placeholder}
                  style={{
                    width: '100%', padding: '12px 16px', borderRadius: '8px',
                    background: 'rgba(255,255,255,0.04)',
                    border: '1px solid rgba(0,180,204,0.2)',
                    color: 'var(--white)', fontSize: '14px', outline: 'none',
                    fontFamily: "'DM Sans',sans-serif", transition: 'border 0.2s'
                  }}
                  onFocus={e => (e.currentTarget.style.borderColor = 'var(--teal)')}
                  onBlur={e => (e.currentTarget.style.borderColor = 'rgba(0,180,204,0.2)')}
                />
              </div>
            ))}

            {[
              { label: 'I AM A...', value: type, onChange: setType, options: ['Retail Investor', 'Real Estate Fund Manager', 'Family Office', 'African Diaspora Investor', 'Institutional Investor', 'Researcher / Academic', 'Other'] },
              { label: 'INVESTMENT INTEREST', value: interest, onChange: setInterest, options: ['FINE5 — Charlotte ($6.85/token)', 'FINE6 — Austin ($12.50/token)', 'Both Properties', 'Analytics Dashboard Only'] },
            ].map(({ label, value, onChange, options }) => (
              <div key={label} style={{ marginBottom: '14px' }}>
                <label style={{ fontSize: '11px', color: 'var(--gray)', display: 'block', marginBottom: '6px', letterSpacing: '0.5px' }}>{label}</label>
                <select
                  value={value}
                  onChange={e => onChange(e.target.value)}
                  style={{
                    width: '100%', padding: '12px 16px', borderRadius: '8px',
                    background: 'var(--navy)',
                    border: '1px solid rgba(0,180,204,0.2)',
                    color: 'var(--white)', fontSize: '14px', outline: 'none',
                    fontFamily: "'DM Sans',sans-serif"
                  }}
                >
                  {options.map(o => <option key={o} value={o}>{o}</option>)}
                </select>
              </div>
            ))}

            <button
              onClick={() => setSubmitted(true)}
              style={{
                width: '100%', padding: '14px', background: 'var(--teal)',
                color: 'var(--navy)', borderRadius: '8px',
                fontSize: '14px', fontWeight: 700, border: 'none',
                cursor: 'pointer', marginTop: '8px', transition: 'all 0.2s'
              }}
              onMouseEnter={e => (e.currentTarget.style.background = 'var(--teal2)')}
              onMouseLeave={e => (e.currentTarget.style.background = 'var(--teal)')}
            >
              Submit Request →
            </button>
          </>
        ) : (
          <div style={{ textAlign: 'center', padding: '20px 0' }}>
            <div style={{ fontSize: '48px', marginBottom: '16px' }}>✓</div>
            <h3 style={{ fontFamily: "'Playfair Display',serif", fontSize: '24px', marginBottom: '12px' }}>Request Received!</h3>
            <p style={{ fontSize: '14px', color: 'var(--gray)', lineHeight: 1.6, marginBottom: '24px' }}>
              Hillary will be in touch within 48 hours.
            </p>
            <a
              href="https://kejafi-stage2.streamlit.app"
              target="_blank"
              rel="noopener noreferrer"
              style={{ color: 'var(--teal)', fontSize: '14px' }}
            >
              → Explore the live demo in the meantime
            </a>
          </div>
        )}
      </div>
    </div>
  )
}
