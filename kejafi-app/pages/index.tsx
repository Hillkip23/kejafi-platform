import { useState } from 'react'
import Head from 'next/head'
import Nav from '../components/Nav'
import Hero from '../components/Hero'
import Stages from '../components/Stages'
import MetroAnalysis from '../components/MetroAnalysis'
import Tokenization from '../components/Tokenization'
import Portfolio from '../components/Portfolio'
import { Waitlist, Footer } from '../components/WaitlistFooter'
import Modal from '../components/Modal'

export default function Home() {
  const [modalOpen, setModalOpen] = useState(false)

  return (
    <>
      <Head>
        <title>Kejafi — Tokenized Real Estate Platform</title>
      </Head>

      <Nav onOpenModal={() => setModalOpen(true)} />
      <Hero onOpenModal={() => setModalOpen(true)} />
      <Stages />
      <MetroAnalysis />
      <Tokenization onOpenModal={() => setModalOpen(true)} />
      <Portfolio />
      <Waitlist />
      <Footer />
      <Modal isOpen={modalOpen} onClose={() => setModalOpen(false)} />
    </>
  )
}
