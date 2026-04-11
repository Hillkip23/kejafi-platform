// lib/web3.ts
import { ethers } from "ethers";
import { FINEPOOL_ABI, ERC20_ABI } from "./abi";

// ===== Environment Variables =====
const RPC_URL = process.env.NEXT_PUBLIC_RPC_URL;
const POOL_ADDRESS = process.env.NEXT_PUBLIC_POOL_ADDRESS;
const FINE5_ADDRESS = process.env.NEXT_PUBLIC_TOKEN0_ADDRESS;
const FINE6_ADDRESS = process.env.NEXT_PUBLIC_TOKEN1_ADDRESS;
const KEJAFI_API_BASE = process.env.NEXT_PUBLIC_KEJAFI_API_BASE ?? "http://127.0.0.1:8000";

// Your tokens have 0 decimals (whole tokens only)
export const TOKEN_DECIMALS = 0;

// ===== Validation =====
function ensureEnvVars(): { rpc: string; pool: string; fine5: string; fine6: string } {
  if (!RPC_URL) throw new Error("NEXT_PUBLIC_RPC_URL not set");
  if (!POOL_ADDRESS) throw new Error("NEXT_PUBLIC_POOL_ADDRESS not set");
  if (!FINE5_ADDRESS) throw new Error("NEXT_PUBLIC_TOKEN0_ADDRESS not set");
  if (!FINE6_ADDRESS) throw new Error("NEXT_PUBLIC_TOKEN1_ADDRESS not set");
  
  return { rpc: RPC_URL, pool: POOL_ADDRESS, fine5: FINE5_ADDRESS, fine6: FINE6_ADDRESS };
}

// ===== Providers & Contracts =====

export function getRpcProvider(): ethers.JsonRpcProvider {
  const { rpc } = ensureEnvVars();
  return new ethers.JsonRpcProvider(rpc);
}

export function getPoolContract(
  providerOrSigner: ethers.Provider | ethers.Signer
) {
  const { pool } = ensureEnvVars();
  return new ethers.Contract(pool, FINEPOOL_ABI, providerOrSigner);
}

export function getFine5Contract(
  providerOrSigner: ethers.Provider | ethers.Signer
) {
  const { fine5 } = ensureEnvVars();
  return new ethers.Contract(fine5, ERC20_ABI, providerOrSigner);
}

export function getFine6Contract(
  providerOrSigner: ethers.Provider | ethers.Signer
) {
  const { fine6 } = ensureEnvVars();
  return new ethers.Contract(fine6, ERC20_ABI, providerOrSigner);
}

// Backward compatibility
export function getErc20(
  address: string,
  providerOrSigner: ethers.Provider | ethers.Signer
) {
  return new ethers.Contract(address, ERC20_ABI, providerOrSigner);
}

// Browser provider for MetaMask
export function getBrowserProvider(): ethers.BrowserProvider {
  if (typeof window === "undefined" || !(window as any).ethereum) {
    throw new Error("No injected Ethereum provider (MetaMask not found)");
  }
  return new ethers.BrowserProvider((window as any).ethereum);
}

export async function getSigner(): Promise<ethers.JsonRpcSigner> {
  const provider = getBrowserProvider();
  await provider.send("eth_requestAccounts", []);
  return provider.getSigner();
}

// ===== API Integration: Fetch Token Addresses (dynamic fallback) =====

export async function fetchTokenAddresses(): Promise<{
  fine5: string;
  fine6: string;
  pool: string;
  chainId: number;
}> {
  // Use env vars as primary source (your .env.local has them)
  const env = ensureEnvVars();
  
  return {
    fine5: env.fine5,
    fine6: env.fine6,
    pool: env.pool,
    chainId: 11155111, // Sepolia
  };
}

// ===== Types =====

export type Reserves = {
  reserve0: number;
  reserve1: number;
  k: number;
  totalSupply: number;
};

export type LPAnalysis = {
  lpBalance: number;
  poolSharePct: number;
  underlying0: number;
  underlying1: number;
};

export type SwapDirection = "0to1" | "1to0";

export type SwapResult = {
  hash: string;
};

// ===== Read functions (for dashboard) =====

export async function fetchOnchainReserves(): Promise<Reserves> {
  const provider = getRpcProvider();
  const pool = getPoolContract(provider);

  const [r0, r1, totalSupply] = await Promise.all([
    pool.reserve0(),
    pool.reserve1(),
    pool.totalSupply(),
  ]);

  const reserve0 = Number(r0);
  const reserve1 = Number(r1);
  const k = reserve0 * reserve1;

  return {
    reserve0,
    reserve1,
    k,
    totalSupply: Number(totalSupply),
  };
}

export async function analyzeLPPosition(
  wallet: string
): Promise<LPAnalysis | null> {
  if (!wallet) return null;

  const provider = getRpcProvider();
  const pool = getPoolContract(provider);

  const [lpBalanceBN, totalSupplyBN, r0, r1] = await Promise.all([
    pool.balanceOf(wallet),
    pool.totalSupply(),
    pool.reserve0(),
    pool.reserve1(),
  ]);

  const lpBalance = Number(lpBalanceBN);
  const totalSupply = Number(totalSupplyBN);

  if (lpBalance === 0 || totalSupply === 0) {
    return {
      lpBalance: 0,
      poolSharePct: 0,
      underlying0: 0,
      underlying1: 0,
    };
  }

  const share = lpBalance / totalSupply;
  const reserve0 = Number(r0);
  const reserve1 = Number(r1);

  return {
    lpBalance,
    poolSharePct: share * 100,
    underlying0: reserve0 * share,
    underlying1: reserve1 * share,
  };
}

// ===== Manual approval helpers =====

export async function approveFine5Max(): Promise<void> {
  const signer = await getSigner();
  const token = getFine5Contract(signer);
  const { pool } = ensureEnvVars();

  const tx = await token.approve(pool, ethers.MaxUint256);
  await tx.wait();
}

export async function approveFine6Max(): Promise<void> {
  const signer = await getSigner();
  const token = getFine6Contract(signer);
  const { pool } = ensureEnvVars();

  const tx = await token.approve(pool, ethers.MaxUint256);
  await tx.wait();
}

// ===== Live swap function (0-decimal SAFE) =====

export async function executeSwap(
  direction: SwapDirection,
  amountIn: number,
  maxSlippagePct: number
): Promise<SwapResult> {
  if (!Number.isFinite(amountIn) || amountIn <= 0) {
    throw new Error("Amount must be a positive number");
  }
  if (!Number.isInteger(amountIn)) {
    amountIn = Math.floor(amountIn);
  }

  const amountInUnits = BigInt(amountIn);

  const signer = await getSigner();
  const signerAddress = await signer.getAddress();

  const pool = getPoolContract(signer);
  const provider = await signer.provider!;
  const readOnlyPool = getPoolContract(provider);

  // Decide which token is input
  const env = ensureEnvVars();
  const inTokenAddress = direction === "0to1" ? env.fine5 : env.fine6;
  const inToken = getErc20(inTokenAddress, signer);

  // ----- 1) Ensure allowance -----
  const currentAllowance: bigint = await inToken.allowance(
    signerAddress,
    env.pool
  );

  if (currentAllowance < amountInUnits) {
    const approveTx = await inToken.approve(env.pool, amountInUnits);
    await approveTx.wait();
  }

  // ----- 2) Compute minOut based on reserves & slippage -----
  const [r0, r1] = await Promise.all([
    readOnlyPool.reserve0(),
    readOnlyPool.reserve1(),
  ]);

  const reserveIn: bigint = direction === "0to1" ? r0 : r1;
  const reserveOut: bigint = direction === "0to1" ? r1 : r0;

  if (reserveIn === 0n || reserveOut === 0n) {
    throw new Error("Pool has no liquidity");
  }

  const FEE_NUM = 997n;
  const FEE_DEN = 1000n;

  const amountInWithFee = (amountInUnits * FEE_NUM) / FEE_DEN;
  const numerator = amountInWithFee * reserveOut;
  const denominator = reserveIn + amountInWithFee;
  const amountOut = numerator / denominator;

  if (amountOut <= 0n) {
    throw new Error("Amount out is zero – check reserves and amount");
  }

  const slippageBps = Math.round(maxSlippagePct * 100);
  const minOut = (amountOut * BigInt(10000 - slippageBps)) / 10000n;

  // ----- 3) Call the correct swap function -----
  let tx;
  if (direction === "0to1") {
    tx = await pool.swapExact0For1(amountInUnits, minOut);
  } else {
    tx = await pool.swapExact1For0(amountInUnits, minOut);
  }

  await tx.wait();
  return { hash: tx.hash };
}