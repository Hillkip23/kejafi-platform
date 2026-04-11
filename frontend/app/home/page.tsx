"use client";

import Link from "next/link";

export default function HomeLanding() {
  return (
    <main className="min-h-screen bg-[#0B0B0B] text-white flex justify-center px-6 py-12">
      <div className="w-full max-w-4xl space-y-12">
        {/* Header */}
        <header className="text-center space-y-3">
          <h1
            className="text-4xl font-extrabold tracking-wide"
            style={{ color: "#046A38" }}
          >
            Fine Finance Ecosystem
          </h1>
          <p className="text-gray-300 text-lg max-w-2xl mx-auto">
            A two-part decentralized finance toolkit built on Sepolia:
            constant-product AMM trading and a full DeFi risk analytics
            dashboard. Styled with UNC Charlotte colors.
          </p>
        </header>

        {/* Two App Cards */}
        <section className="grid grid-cols-1 md:grid-cols-2 gap-8">
          {/* Card 1: Trading & Liquidity */}
          <div className="p-6 rounded-2xl border border-[#1F2937] bg-[#111] shadow-xl flex flex-col justify-between">
            <div className="space-y-3">
              <div className="text-xs font-semibold uppercase text-[#BBF7D0]">
                Execution Layer
              </div>
              <h2 className="text-xl font-bold">FinePool Swap &amp; Liquidity</h2>
              <p className="text-gray-300 text-sm">
                Swap between FINE5 and FINE6, add or remove liquidity,
                and interact directly with your deployed AMM pool.
              </p>
            </div>

            <Link
              href="https://fine-lp-swap-qwqh.vercel.app/"
              target="_blank"
              className="mt-6 py-3 px-4 rounded-xl font-semibold text-center"
              style={{
                backgroundColor: "#046A38",
                color: "white",
                boxShadow: "0 0 10px rgba(4,106,56,0.5)",
              }}
            >
              🚀 Open Trading & Liquidity App
            </Link>
          </div>

          {/* Card 2: Risk Dashboard */}
          <div className="p-6 rounded-2xl border border-[#1F2937] bg-[#111] shadow-xl flex flex-col justify-between">
            <div className="space-y-3">
              <div className="text-xs font-semibold uppercase text-[#FDE68A]">
                Analytics Layer
              </div>
              <h2 className="text-xl font-bold">DeFi Risk Dashboard</h2>
              <p className="text-gray-300 text-sm">
                Analyze price impact, impermanent loss, LP positions,
                slippage risk, and live on-chain pool metrics.
              </p>
            </div>

            <Link
              href="https://defi1-risk-3s82.vercel.app/"
              target="_blank"
              className="mt-6 py-3 px-4 rounded-xl font-semibold text-center"
              style={{
                backgroundColor: "#A49665",
                color: "#111",
                boxShadow: "0 0 10px rgba(164,150,101,0.4)",
              }}
            >
              📊 Open Risk Analytics Dashboard
            </Link>
          </div>
        </section>

        {/* Footer */}
        <footer className="text-center text-xs text-gray-500 mt-10">
          © 2024 Fine Finance · Built with UNC Charlotte colors · Sepolia testnet
        </footer>
      </div>
    </main>
  );
}

