import { useState, useEffect } from 'react'

interface NavProps {
  onOpenModal: () => void
}

export default function Nav({ onOpenModal }: NavProps) {
  const [scrolled, setScrolled] = useState(false)
  const [active, setActive] = useState('home')

  useEffect(() => {
    const handleScroll = () => {
      setScrolled(window.scrollY > 20)
      const sections = ['home', 'stages', 'metro', 'tokenize', 'portfolio', 'waitlist']
      for (const id of sections) {
        const el = document.getElementById(id)
        if (el) {
          const rect = el.getBoundingClientRect()
          if (rect.top <= 100 && rect.bottom > 100) { setActive(id); break }
        }
      }
    }
    window.addEventListener('scroll', handleScroll)
    return () => window.removeEventListener('scroll', handleScroll)
  }, [])

  const navTo = (id: string) => {
    document.getElementById(id)?.scrollIntoView({ behavior: 'smooth' })
  }

  return (
    <nav style={{
      position: 'fixed', top: 0, left: 0, right: 0, zIndex: 1000,
      display: 'flex', alignItems: 'center', padding: '0 48px',
      height: '64px',
      background: scrolled ? 'rgba(13,27,62,0.97)' : 'rgba(13,27,62,0.85)',
      backdropFilter: 'blur(20px)',
      borderBottom: '1px solid rgba(0,180,204,0.12)',
      transition: 'all 0.3s'
    }}>
      <div
        onClick={() => navTo('home')}
        style={{
          fontFamily: "'Playfair Display', serif",
          fontSize: '22px', fontWeight: 900,
          color: 'var(--teal)', letterSpacing: '1px',
          marginRight: 'auto', cursor: 'pointer'
        }}
      >
        KEJAFI
      </div>

      <div style={{ display: 'flex', gap: '4px', alignItems: 'center' }}>
        {[
          { id: 'stages', label: 'Platform' },
          { id: 'metro', label: 'Stage 1' },
          { id: 'tokenize', label: 'Stage 2' },
          { id: 'portfolio', label: 'Stage 3' },
          { id: 'waitlist', label: 'Join' },
        ].map(({ id, label }) => (
          <button
            key={id}
            onClick={() => navTo(id)}
            style={{
              padding: '8px 16px', borderRadius: '6px',
              fontSize: '13px', fontWeight: 500,
              color: active === id ? 'var(--teal)' : 'var(--gray)',
              background: active === id ? 'rgba(0,180,204,0.08)' : 'transparent',
              border: 'none', cursor: 'pointer', transition: 'all 0.2s'
            }}
          >
            {label}
          </button>
        ))}
        <button
          onClick={onOpenModal}
          style={{
            marginLeft: '12px', padding: '9px 20px',
            background: 'var(--teal)', color: 'var(--navy)',
            borderRadius: '6px', fontSize: '13px', fontWeight: 700,
            border: 'none', cursor: 'pointer', transition: 'all 0.2s'
          }}
        >
          Get Access
        </button>
      </div>
    </nav>
  )
}
