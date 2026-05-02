import { Html, Head, Main, NextScript } from 'next/document'

export default function Document() {
  return (
    <Html lang="en">
      <Head>
        <meta charSet="UTF-8" />
        <meta name="description" content="Kejafi — Tokenized Real Estate Platform. End-to-end platform bridging institutional-grade quantitative finance with live DeFi infrastructure." />
        <meta property="og:title" content="Kejafi — Tokenized Real Estate" />
        <meta property="og:description" content="OU rent modelling → ERC-20 deployment → Monte Carlo portfolio analytics" />
        <meta name="theme-color" content="#0D1B3E" />
        <link rel="icon" href="/favicon.ico" />
      </Head>
      <body>
        <Main />
        <NextScript />
      </body>
    </Html>
  )
}
