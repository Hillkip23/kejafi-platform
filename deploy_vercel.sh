#!/usr/bin/env bash
set -euo pipefail

cd "$(dirname "$0")/frontend"

echo "Deploying frontend to Vercel..."
echo "Make sure NEXT_PUBLIC_KEJAFI_API_BASE is set in Vercel project settings."

npx vercel --prod
