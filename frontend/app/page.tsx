"use client";

import { useEffect, useState } from "react";
import {
  fetchOnchainReserves,
  analyzeLPPosition,
  executeSwap,
  getSigner,
  getErc20,
  fetchTokenAddresses,
  type SwapDirection,
} from "../lib/web3";

// ---------- Token labels ----------

const TOKEN0_LABEL = "Kejafi Property A (FINE5)";
const TOKEN1_LABEL = "Kejafi Property B (FINE6)";
const LP_LABEL = "Kejafi Property A/B LP (F5F6-LP)";

// ---------- Kejafi fundamentals ----------

type KejafiFundamentals = {
  id: string;
  address: string;
  list_price: number | null;
  token_price: number | null;
  total_supply: number | null;
  cap_rate: number | null;
  risk_bucket?: string | null;
};

type TokenInfo = {
  fine5: string;
  fine6: string;
  pool: string;
  chainId: number;
};

const KEJAFI_API_BASE =
  process.env.NEXT_PUBLIC_KEJAFI_API_BASE ?? "http://127.0.0.1:8000";

const PROP_A_ID = "charlotte_mfk_001"; // maps to FINE5
const PROP_B_ID = "charlotte_mfk_002"; // maps to FINE6

// ---------- Local AMM math (for risk calc only) ----------

const FEE_NUM = 997; // 0.3% fee
const FEE_DEN = 1000;

function getSwapOutput(reserveIn: number, reserveOut: number, amountIn: number) {
  if (amountIn <= 0 || reserveIn <= 0 || reserveOut <= 0) return 0;

  const amountInWithFee = (amountIn * FEE_NUM) / FEE_DEN;
  const numerator = amountInWithFee * reserveOut;
  const denominator = reserveIn + amountInWithFee;
  return numerator / denominator;
}

function getPriceImpactPercent(
  reserveIn: number,
  reserveOut: number,
  amountIn: number
) {
  if (amountIn <= 0 || reserveIn <= 0 || reserveOut <= 0) return 0;

  const spotPrice = reserveOut / reserveIn;
  const amountOut = getSwapOutput(reserveIn, reserveOut, amountIn);
  const executionPrice = amountOut / amountIn;
  const impact = (executionPrice - spotPrice) / spotPrice;
  return impact * 100;
}

// Impermanent loss approximation for a standard x·y=k AMM
function computeImpermanentLoss(percentChangeTokenA: number) {
  const p = 1 + percentChangeTokenA / 100; // price ratio
  if (p <= 0) return 0;
  const hodl = (1 + p) / 2;
  const lp = Math.sqrt(p);
  return ((lp - hodl) / hodl) * 100; // %
}

// ---------- React component ----------

export default function HomePage() {
  // Pool reserves
  const [reserve0, setReserve0] = useState(101131);
  const [reserve1, setReserve1] = useState(99493);
  const [kValue, setKValue] = useState<number | null>(null);
  const [totalLpSupply, setTotalLpSupply] = useState<number | null>(null);
  const [reservesSource, setReservesSource] = useState<
    "demo" | "onchain" | "error"
  >("demo");
  const [reservesError, setReservesError] = useState<string | null>(null);

  // Wallet / connection
  const [walletAddress, setWalletAddress] = useState<string | null>(null);
  const [connectError, setConnectError] = useState<string | null>(null);

  // Token addresses (dynamic from API)
  const [tokenInfo, setTokenInfo] = useState<TokenInfo | null>(null);
  const [tokenInfoLoading, setTokenInfoLoading] = useState(true);

  // Swap inputs
  const [direction, setDirection] = useState<SwapDirection>("0to1");
  const [amountIn, setAmountIn] = useState("100");

  // Risk output
  const [amountOut, setAmountOut] = useState<number | null>(null);
  const [priceImpact, setPriceImpact] = useState<number | null>(null);
  const [swapSafety, setSwapSafety] = useState<string>("");

  // On-chain swap status
  const [isSwapping, setIsSwapping] = useState(false);
  const [swapStatus, setSwapStatus] = useState<string | null>(null);
  const [swapError, setSwapError] = useState<string | null>(null);

  // Approvals
  const [approving, setApproving] = useState<"FINE5" | "FINE6" | null>(null);
  const [approveMessage, setApproveMessage] = useState<string | null>(null);
  const [approveError, setApproveError] = useState<string | null>(null);

  // Impermanent loss scenario
  const [ilChange, setIlChange] = useState("50");
  const [ilResult, setIlResult] = useState<number | null>(null);

  // LP Analyzer
  const [lpWallet, setLpWallet] = useState(
    "0x581EE242cF8e8889E2fa37Bd7C2716d788f051af"
  );
  const [lpBalance, setLpBalance] = useState<number | null>(null);
  const [lpSharePct, setLpSharePct] = useState<number | null>(null);
  const [lpUnderlying0, setLpUnderlying0] = useState<number | null>(null);
  const [lpUnderlying1, setLpUnderlying1] = useState<number | null>(null);
  const [lpStatus, setLpStatus] = useState<string | null>(null);
  const [lpError, setLpError] = useState<string | null>(null);

  // Kejafi fundamentals
  const [fundamentalsA, setFundamentalsA] =
    useState<KejafiFundamentals | null>(null);
  const [fundamentalsB, setFundamentalsB] =
    useState<KejafiFundamentals | null>(null);

  // -------- Load on-chain reserves and token addresses on mount --------

  useEffect(() => {
    async function loadInitialData() {
      // Load reserves
      try {
        const r = await fetchOnchainReserves();
        setReserve0(r.reserve0);
        setReserve1(r.reserve1);
        setKValue(r.k);
        setTotalLpSupply(r.totalSupply);
        setReservesSource("onchain");
        setReservesError(null);
      } catch (err: any) {
        console.error("Failed to load on-chain reserves", err);
        setReservesSource("error");
        setReservesError("Failed to load on-chain reserves. Using demo values.");
        setKValue(reserve0 * reserve1);
      }

      // Load token addresses from API
      try {
        setTokenInfoLoading(true);
        const addresses = await fetchTokenAddresses();
        setTokenInfo(addresses);
      } catch (err) {
        console.error("Failed to fetch token addresses:", err);
        // Will use fallbacks from web3.ts
      } finally {
        setTokenInfoLoading(false);
      }
    }
    loadInitialData();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  // -------- Load Kejafi fundamentals for A and B --------

  useEffect(() => {
    async function loadFundamentals() {
      try {
        const [resA, resB] = await Promise.all([
          fetch(`${KEJAFI_API_BASE}/properties/${PROP_A_ID}`),
          fetch(`${KEJAFI_API_BASE}/properties/${PROP_B_ID}`),
        ]);

        if (!resA.ok || !resB.ok) {
          throw new Error(`HTTP ${resA.status}/${resB.status}`);
        }

        const dataA = await resA.json();
        const dataB = await resB.json();

        setFundamentalsA({
          id: dataA.id,
          address: dataA.address,
          list_price: dataA.list_price,
          token_price: dataA.token_price,
          total_supply: dataA.total_supply,
          cap_rate: dataA.cap_rate,
          risk_bucket: dataA.risk_bucket,
        });

        setFundamentalsB({
          id: dataB.id,
          address: dataB.address,
          list_price: dataB.list_price,
          token_price: dataB.token_price,
          total_supply: dataB.total_supply,
          cap_rate: dataB.cap_rate,
          risk_bucket: dataB.risk_bucket,
        });
      } catch (e) {
        console.error("Failed to load Kejafi fundamentals", e);
      }
    }

    loadFundamentals();
  }, []);

  // -------- Connect wallet --------

  async function handleConnectWallet() {
    try {
      setConnectError(null);
      const signer = await getSigner();
      const addr = await signer.getAddress();
      setWalletAddress(addr);
    } catch (err: any) {
      console.error(err);
      setConnectError(err.message ?? "Failed to connect wallet");
    }
  }

  // -------- Local risk calculation (no chain tx) --------

  function handleCalculateRisk() {
    const amt = Number(amountIn);
    if (isNaN(amt) || amt <= 0) {
      setAmountOut(null);
      setPriceImpact(null);
      setSwapSafety("");
      return;
    }

    const [rIn, rOut] =
      direction === "0to1" ? [reserve0, reserve1] : [reserve1, reserve0];

    const out = getSwapOutput(rIn, rOut, amt);
    const impact = getPriceImpactPercent(rIn, rOut, amt);

    setAmountOut(out);
    setPriceImpact(impact);

    const absImpact = Math.abs(impact);
    let label = "";
    if (absImpact < 1) label = "Excellent";
    else if (absImpact < 3) label = "Good";
    else if (absImpact < 10) label = "Caution";
    else label = "High Risk";

    setSwapSafety(label);
  }

  // -------- On-chain swap --------

  async function handleExecuteSwap() {
    const amt = Number(amountIn);
    if (isNaN(amt) || amt <= 0) {
      setSwapError("Enter a valid amount to swap");
      setSwapStatus(null);
      return;
    }

    setSwapError(null);
    setSwapStatus(null);
    setIsSwapping(true);

    try {
      const result = await executeSwap(direction, amt, 1);
      setSwapStatus(
        `Swap executed! Tx: ${result.hash.substring(0, 10)}... (check Etherscan)`
      );
    } catch (err: any) {
      console.error(err);
      setSwapError(err.reason || err.message || "Swap failed");
      setSwapStatus(null);
    } finally {
      setIsSwapping(false);
    }
  }

  // -------- Approve tokens for FinePool (dynamic addresses) --------

  async function handleApprove(which: "FINE5" | "FINE6") {
    if (!tokenInfo) {
      setApproveError("Token addresses not loaded yet");
      return;
    }

    setApproveMessage(null);
    setApproveError(null);
    setApproving(which);
    
    try {
      const signer = await getSigner();
      const tokenAddress = which === "FINE5" ? tokenInfo.fine5 : tokenInfo.fine6;
      const token = getErc20(tokenAddress, signer);

      const approveAmount = BigInt(1_000_000);

      const tx = await token.approve(tokenInfo.pool, approveAmount);
      await tx.wait();

      setApproveMessage(
        `${which} approved for FinePool. You can now swap using that token.`
      );
    } catch (err: any) {
      console.error(err);
      setApproveError(err.reason || err.message || "Approve failed");
    } finally {
      setApproving(null);
    }
  }

  // -------- Impermanent loss scenario --------

  function handleCalculateIL() {
    const pct = Number(ilChange);
    if (isNaN(pct)) {
      setIlResult(null);
      return;
    }
    const il = computeImpermanentLoss(pct);
    setIlResult(il);
  }

  // -------- LP Position analyzer --------

  async function handleAnalyzeLP() {
    setLpStatus(null);
    setLpError(null);
    try {
      const res = await analyzeLPPosition(lpWallet);
      if (!res) {
        setLpStatus("No LP tokens found for that address.");
        setLpBalance(0);
        setLpSharePct(0);
        setLpUnderlying0(0);
        setLpUnderlying1(0);
        return;
      }

      setLpBalance(res.lpBalance);
      setLpSharePct(res.poolSharePct);
      setLpUnderlying0(res.underlying0);
      setLpUnderlying1(res.underlying1);
      setLpStatus("LP position loaded.");
    } catch (err: any) {
      console.error(err);
      setLpError(err.message ?? "Failed to analyze LP position");
    }
  }

  // ---------- Render ----------

  return (
    <main className="min-h-screen bg-black text-white flex justify-center px-4 py-10">
      <div className="w-full max-w-5xl space-y-8">
        {/* Header */}
        <header className="space-y-2">
          <h1 className="text-3xl font-bold">
            Kejafi Property AMM – Swap Risk Analyzer
          </h1>
          <p className="text-sm text-gray-300">
            Constant-product AMM math (x · y = k) with a 0.3% fee. Reserves are
            pulled from your FinePool on Sepolia when available.
          </p>
          {tokenInfoLoading && (
            <p className="text-xs text-blue-400">Loading token addresses...</p>
          )}
        </header>

        {/* About / How It Works */}
        <section className="w-full bg-[#111] border border-[#222] rounded-xl p-6 mt-1">
          <h2 className="text-2xl font-bold mb-3">About This Dashboard</h2>

          <p className="text-gray-300 leading-relaxed mb-4">
            This dashboard provides real-time risk analysis and on-chain swap
            execution for the{" "}
            <strong>
              {TOKEN0_LABEL} / {TOKEN1_LABEL}
            </strong>{" "}
            liquidity pool on Sepolia. It uses constant-product AMM math (
            <code>x · y = k</code>) and interacts directly with your deployed
            FinePool smart contract.
          </p>

          <h3 className="text-xl font-semibold mt-4 mb-2">How It Works</h3>
          <ul className="list-disc pl-6 text-gray-300 space-y-2">
            <li>
              <strong>Pool Reserves</strong> show on-chain {TOKEN0_LABEL} and{" "}
              {TOKEN1_LABEL} balances and compute the invariant (<code>k</code>)
              and total LP supply.
            </li>
            <li>
              <strong>Risk Calculator</strong> simulates swaps using exact AMM
              math, including the 0.3% fee, and estimates expected output,
              slippage, and swap safety.
            </li>
            <li>
              <strong>Token Approvals</strong> allow your wallet to authorize
              the FinePool contract to spend FINE5/FINE6 before executing a
              swap.
            </li>
            <li>
              <strong>On-Chain Swaps</strong> are executed directly through your
              FinePool contract using MetaMask, respecting slippage settings.
            </li>
            <li>
              <strong>LP Analyzer</strong> checks your {LP_LABEL} balance and
              computes your underlying property token holdings based on your
              percentage of the pool.
            </li>
            <li>
              <strong>Visualizations</strong> show price impact across trade
              sizes and impermanent-loss curves for different market
              conditions.
            </li>
          </ul>

          <p className="text-gray-400 mt-4 text-sm">
            This tool is designed for educational and experimental use only. All
            values are estimates based on current reserves on Sepolia.
          </p>
        </section>

        {/* Pool Reserves */}
        <section className="border border-gray-700 rounded-xl p-4 bg-zinc-900 space-y-4">
          <div className="flex items-center justify-between">
            <div className="space-y-1">
              <h2 className="font-semibold text-lg">Pool Reserves</h2>
              <p className="text-xs text-gray-400">
                Source:{" "}
                {reservesSource === "onchain"
                  ? "On-chain (Sepolia)"
                  : reservesSource === "error"
                  ? "Local demo (failed to load on-chain reserves)"
                  : "Local demo"}
              </p>
              {reservesError && (
                <p className="text-xs text-amber-400">{reservesError}</p>
              )}
            </div>
            <div className="text-right text-xs text-gray-400 space-y-1">
              <div>
                k = x · y ≈{" "}
                {kValue !== null ? kValue.toLocaleString() : "calculating..."}
              </div>
              <div>
                Total LP Supply:{" "}
                {totalLpSupply !== null
                  ? totalLpSupply.toLocaleString()
                  : "—"}
              </div>
            </div>
          </div>

          <div className="grid grid-cols-2 gap-4 text-sm">
            <div className="flex flex-col gap-1">
              <label className="text-gray-300">
                Reserve0 ({TOKEN0_LABEL})
              </label>
              <input
                className="bg-zinc-800 border border-gray-600 rounded px-2 py-1 text-sm text-white"
                value={reserve0}
                onChange={(e) => setReserve0(Number(e.target.value) || 0)}
              />
            </div>
            <div className="flex flex-col gap-1">
              <label className="text-gray-300">
                Reserve1 ({TOKEN1_LABEL})
              </label>
              <input
                className="bg-zinc-800 border border-gray-600 rounded px-2 py-1 text-sm text-white"
                value={reserve1}
                onChange={(e) => setReserve1(Number(e.target.value) || 0)}
              />
            </div>
          </div>
        </section>

        {/* Swap Inputs */}
        <section className="border border-gray-700 rounded-xl p-4 bg-zinc-900 space-y-4">
          <div className="flex items-center justify-between">
            <h2 className="font-semibold text-lg">Swap Inputs</h2>
            <button
              onClick={handleConnectWallet}
              className="text-xs px-3 py-1 rounded-lg border border-emerald-500 text-emerald-300 hover:bg-emerald-600/20"
            >
              {walletAddress
                ? `Wallet: ${walletAddress.slice(0, 6)}...${walletAddress.slice(
                    -4
                  )}`
                : "Connect Wallet"}
            </button>
          </div>

          {walletAddress && (
            <p className="text-xs text-amber-300">
              Connected to MetaMask. You can Approve tokens and Execute swaps
              on-chain.
            </p>
          )}
          {connectError && (
            <p className="text-xs text-red-400">Connect error: {connectError}</p>
          )}

          <div className="space-y-3">
            {/* Direction */}
            <div className="flex flex-col gap-2">
              <label className="text-sm text-gray-300">
                Direction (which way are you swapping?)
              </label>
              <div className="flex gap-3 text-sm">
                <button
                  className={`px-3 py-1 rounded-lg border ${
                    direction === "0to1"
                      ? "bg-emerald-600 border-emerald-500"
                      : "border-gray-600"
                  }`}
                  onClick={() => setDirection("0to1")}
                >
                  {TOKEN0_LABEL} → {TOKEN1_LABEL}
                </button>
                <button
                  className={`px-3 py-1 rounded-lg border ${
                    direction === "1to0"
                      ? "bg-emerald-600 border-emerald-500"
                      : "border-gray-600"
                  }`}
                  onClick={() => setDirection("1to0")}
                >
                  {TOKEN1_LABEL} → {TOKEN0_LABEL}
                </button>
              </div>
            </div>

            {/* Amount In */}
            <div className="flex flex-col gap-2">
              <label className="text-sm text-gray-300">Amount In</label>
              <input
                className="bg-zinc-800 border border-gray-600 rounded px-3 py-2 text-sm text-white"
                value={amountIn}
                onChange={(e) => setAmountIn(e.target.value)}
                placeholder="e.g. 5"
              />
            </div>

            {/* Approve buttons */}
            <div className="flex flex-wrap gap-3 items-center text-xs">
              <span className="text-gray-300">Token approvals:</span>
              <button
                disabled={!walletAddress || approving === "FINE5" || !tokenInfo}
                onClick={() => handleApprove("FINE5")}
                className={`px-3 py-1 rounded-lg border ${
                  approving === "FINE5"
                    ? "border-blue-500 bg-blue-600/30"
                    : "border-gray-600 hover:border-blue-400"
                } disabled:opacity-50 disabled:cursor-not-allowed`}
              >
                {approving === "FINE5"
                  ? `Approving ${TOKEN0_LABEL}...`
                  : `Approve ${TOKEN0_LABEL}`}
              </button>
              <button
                disabled={!walletAddress || approving === "FINE6" || !tokenInfo}
                onClick={() => handleApprove("FINE6")}
                className={`px-3 py-1 rounded-lg border ${
                  approving === "FINE6"
                    ? "border-blue-500 bg-blue-600/30"
                    : "border-gray-600 hover:border-blue-400"
                } disabled:opacity-50 disabled:cursor-not-allowed`}
              >
                {approving === "FINE6"
                  ? `Approving ${TOKEN1_LABEL}...`
                  : `Approve ${TOKEN1_LABEL}`}
              </button>
            </div>
            {!tokenInfo && (
              <p className="text-xs text-amber-400">
                Token addresses loading... (using fallbacks if API unavailable)
              </p>
            )}
            {approveMessage && (
              <p className="text-xs text-emerald-400">{approveMessage}</p>
            )}
            {approveError && (
              <p className="text-xs text-red-400">
                Approve error: {approveError}
              </p>
            )}

            {/* Action buttons */}
            <div className="flex flex-wrap gap-3 mt-2">
              <button
                onClick={handleCalculateRisk}
                className="px-4 py-2 rounded-lg bg-emerald-600 hover:bg-emerald-500 text-sm font-semibold"
              >
                Calculate Risk
              </button>
              <button
                onClick={handleExecuteSwap}
                disabled={!walletAddress || isSwapping}
                className="px-4 py-2 rounded-lg bg-indigo-600 hover:bg-indigo-500 text-sm font-semibold disabled:opacity-50 disabled:cursor-not-allowed"
              >
                {isSwapping ? "Swapping..." : "Execute Swap On-Chain"}
              </button>
            </div>

            {swapStatus && (
              <p className="text-xs text-emerald-400 mt-1">{swapStatus}</p>
            )}
            {swapError && (
              <p className="text-xs text-red-400 mt-1">
                Swap failed: {swapError}
              </p>
            )}
          </div>

          {/* Fundamentals (from Kejafi API) */}
          <div className="mt-4 border-t border-gray-700 pt-4 text-xs text-gray-300 space-y-2">
            <h3 className="text-sm font-semibold text-gray-200">
              Property Fundamentals (Kejafi)
            </h3>
            {fundamentalsA && fundamentalsB ? (
              <>
                <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
                  <div className="space-y-1">
                    <div className="font-semibold">
                      {TOKEN0_LABEL} – {fundamentalsA.id}
                    </div>
                    <div className="text-gray-400">
                      {fundamentalsA.address}
                    </div>
                    <div>
                      List price: $
                      {(fundamentalsA.list_price ?? 0).toLocaleString(
                        undefined,
                        { maximumFractionDigits: 0 }
                      )}
                    </div>
                    <div>
                      Token price: $
                      {(fundamentalsA.token_price ?? 0).toFixed(2)}
                    </div>
                    <div>
                      Total supply:{" "}
                      {(fundamentalsA.total_supply ?? 0).toLocaleString(
                        undefined,
                        { maximumFractionDigits: 0 }
                      )}
                    </div>
                    <div>
                      Cap rate:{" "}
                      {((fundamentalsA.cap_rate ?? 0) * 100).toFixed(2)}%
                    </div>
                    {fundamentalsA.risk_bucket && (
                      <div>Risk bucket: {fundamentalsA.risk_bucket}</div>
                    )}
                  </div>

                  <div className="space-y-1">
                    <div className="font-semibold">
                      {TOKEN1_LABEL} – {fundamentalsB.id}
                    </div>
                    <div className="text-gray-400">
                      {fundamentalsB.address}
                    </div>
                    <div>
                      List price: $
                      {(fundamentalsB.list_price ?? 0).toLocaleString(
                        undefined,
                        { maximumFractionDigits: 0 }
                      )}
                    </div>
                    <div>
                      Token price: $
                      {(fundamentalsB.token_price ?? 0).toFixed(2)}
                    </div>
                    <div>
                      Total supply:{" "}
                      {(fundamentalsB.total_supply ?? 0).toLocaleString(
                        undefined,
                        { maximumFractionDigits: 0 }
                      )}
                    </div>
                    <div>
                      Cap rate:{" "}
                      {((fundamentalsB.cap_rate ?? 0) * 100).toFixed(2)}%
                    </div>
                    {fundamentalsB.risk_bucket && (
                      <div>Risk bucket: {fundamentalsB.risk_bucket}</div>
                    )}
                  </div>
                </div>
                <p className="text-[10px] text-gray-500">
                  Property A (FINE5) = {PROP_A_ID}. Property B (FINE6) ={" "}
                  {PROP_B_ID}. Fundamentals come from the Kejafi API; AMM
                  prices may deviate from NAV.
                </p>
              </>
            ) : (
              <p className="text-[11px] text-gray-500">
                Loading Kejafi fundamentals for Property A and B…
              </p>
            )}
          </div>
        </section>

        {/* Risk Output */}
        <section className="border border-gray-700 rounded-xl p-4 bg-zinc-900 space-y-4">
          <h2 className="font-semibold text-lg">Risk Output</h2>

          {amountOut === null && priceImpact === null ? (
            <p className="text-sm text-gray-400">
              Enter an amount and click <strong>Calculate Risk</strong> to see
              expected output and price impact.
            </p>
          ) : (
            <div className="grid grid-cols-3 gap-4 text-sm">
              <div>
                <div className="text-gray-400">Expected Output</div>
                <div className="font-mono text-base">
                  {amountOut !== null ? amountOut.toFixed(6) : "—"}
                </div>
              </div>
              <div>
                <div className="text-gray-400">Price Impact</div>
                <div className="font-mono text-base">
                  {priceImpact !== null
                    ? priceImpact.toFixed(4) + "%"
                    : "—"}
                </div>
              </div>
              <div>
                <div className="text-gray-400">Swap Safety</div>
                <div className="font-semibold">
                  {swapSafety || "Run a calculation"}
                </div>
              </div>
            </div>
          )}
        </section>

        {/* Impermanent Loss Scenario */}
        <section className="border border-gray-700 rounded-xl p-4 bg-zinc-900 space-y-4">
          <h2 className="font-semibold text-lg">
            Impermanent Loss Scenario ({TOKEN0_LABEL} price change)
          </h2>
          <p className="text-xs text-gray-400">
            Enter a hypothetical percentage change in {TOKEN0_LABEL} price
            relative to {TOKEN1_LABEL} (e.g. +50, -30). This approximates IL for
            a standard x·y=k AMM.
          </p>
          <div className="flex flex-wrap items-end gap-3">
            <div className="flex flex-col gap-2">
              <label className="text-sm text-gray-300">
                {TOKEN0_LABEL} price change (%)
              </label>
              <input
                className="bg-zinc-800 border border-gray-600 rounded px-3 py-2 text-sm text-white"
                value={ilChange}
                onChange={(e) => setIlChange(e.target.value)}
              />
            </div>
            <button
              onClick={handleCalculateIL}
              className="px-4 py-2 rounded-lg bg-emerald-600 hover:bg-emerald-500 text-sm font-semibold"
            >
              Calculate IL
            </button>
          </div>
          {ilResult !== null && (
            <p className="text-sm text-gray-200">
              Impermanent Loss vs HODL:{" "}
              <span
                className={
                  ilResult <= 0 ? "text-red-400 font-mono" : "text-emerald-400"
                }
              >
                {ilResult.toFixed(4)}%
              </span>
            </p>
          )}
        </section>

        {/* LP Position Analyzer */}
        <section className="border border-gray-700 rounded-xl p-4 bg-zinc-900 space-y-4">
          <h2 className="font-semibold text-lg">LP Position Analyzer</h2>
          <p className="text-xs text-gray-400">
            Enter any wallet address that holds {LP_LABEL} tokens on your
            FinePool contract. This estimates the underlying {TOKEN0_LABEL} and{" "}
            {TOKEN1_LABEL} in that position.
          </p>

          <div className="flex flex-wrap items-end gap-3">
            <div className="flex flex-col flex-1 gap-2">
              <label className="text-sm text-gray-300">Wallet address</label>
              <input
                className="bg-zinc-800 border border-gray-600 rounded px-3 py-2 text-sm text-white w-full"
                value={lpWallet}
                onChange={(e) => setLpWallet(e.target.value)}
                placeholder="0x..."
              />
            </div>
            <button
              onClick={handleAnalyzeLP}
              className="px-4 py-2 rounded-lg bg-emerald-600 hover:bg-emerald-500 text-sm font-semibold"
            >
              Analyze LP Position
            </button>
          </div>

          {lpStatus && <p className="text-xs text-emerald-400">{lpStatus}</p>}
          {lpError && <p className="text-xs text-red-400">{lpError}</p>}

          {lpBalance !== null && (
            <div className="grid grid-cols-3 gap-4 text-sm mt-2">
              <div>
                <div className="text-gray-400">LP Token Balance</div>
                <div className="font-mono text-base">
                  {lpBalance.toLocaleString(undefined, {
                    maximumFractionDigits: 6,
                  })}
                </div>
              </div>
              <div>
                <div className="text-gray-400">Pool Share</div>
                <div className="font-mono text-base">
                  {lpSharePct !== null ? lpSharePct.toFixed(6) + "%" : "—"}
                </div>
              </div>
              <div>
                <div className="text-gray-400">Underlying Tokens</div>
                <div className="font-mono text-base">
                  {lpUnderlying0 !== null && lpUnderlying1 !== null
                    ? `${lpUnderlying0.toFixed(6)} Kejafi A / ${lpUnderlying1.toFixed(
                        6
                      )} Kejafi B`
                    : "—"}
                </div>
              </div>
            </div>
          )}
        </section>
      </div>

      <footer className="fixed bottom-2 left-0 right-0 px-4 text-xs text-gray-500 text-center">
        {tokenInfo ? (
          <>
            <div>FINE5 (Kejafi Property A): {tokenInfo.fine5}</div>
            <div>FINE6 (Kejafi Property B): {tokenInfo.fine6}</div>
            <div>FinePool (AMM): {tokenInfo.pool}</div>
            <div className="text-[10px] mt-1 text-gray-600">
              Chain ID: {tokenInfo.chainId} (Sepolia)
            </div>
          </>
        ) : (
          <>
            <div>Loading contract addresses from Kejafi API...</div>
            <div className="text-[10px] mt-1 text-gray-600">
              Using fallbacks if API unavailable
            </div>
          </>
        )}
      </footer>
    </main>
  );
}