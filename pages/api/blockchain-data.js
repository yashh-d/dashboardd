import { kv } from '@vercel/kv';

// Dictionary mapping blockchain names to their identifiers in DeFiLlama and CoinGecko
const BLOCKCHAIN_MAPPING = {
  "Aptos": {"defillama": "aptos", "coingecko": "aptos"},
  "Avalanche": {"defillama": "Avalanche", "coingecko": "avalanche-2"},
  "Core DAO": {"defillama": "core", "coingecko": "coredaoorg"},
  "Flow": {"defillama": "flow", "coingecko": "flow"},
  "Injective": {"defillama": "injective", "coingecko": "injective-protocol"},
  "Optimism": {"defillama": "optimism", "coingecko": "optimism"},
  "Polygon": {"defillama": "polygon", "coingecko": "matic-network"},
  "XRP/XRPL": {"defillama": "XRPL", "coingecko": "ripple"},
  "Sei": {"defillama": "sei", "coingecko": "sei-network"}
};

// Fetch TVL data from DeFiLlama
async function fetchTvlData(blockchainId) {
  try {
    const url = `https://api.llama.fi/v2/historicalChainTvl/${blockchainId}`;
    const response = await fetch(url);
    
    if (response.status === 200) {
      const data = await response.json();
      return data.map(item => ({
        date: new Date(item.date * 1000).toISOString(),
        tvl: item.tvl
      }));
    } else {
      console.error(`Error fetching TVL data for ${blockchainId}: ${response.status}`);
      return [];
    }
  } catch (error) {
    console.error(`Exception when fetching TVL data for ${blockchainId}:`, error);
    return [];
  }
}

// Fetch price data from CoinGecko
async function fetchPriceData(coinId) {
  try {
    const url = `https://api.coingecko.com/api/v3/coins/${coinId}/market_chart`;
    const params = new URLSearchParams({
      vs_currency: 'usd',
      days: '90',
      interval: 'daily'
    });
    
    const response = await fetch(`${url}?${params}`);
    
    if (response.status === 200) {
      const data = await response.json();
      const prices = data.prices || [];
      
      return prices.map(([timestamp, price]) => ({
        date: new Date(timestamp).toISOString(),
        timestamp,
        price
      }));
    } else {
      console.error(`Error fetching price data for ${coinId}: ${response.status}`);
      return [];
    }
  } catch (error) {
    console.error(`Exception when fetching price data for ${coinId}:`, error);
    return [];
  }
}

export default async function handler(req, res) {
  // Check if we have recent data in KV store
  const cachedData = await kv.get('blockchain_data');
  const lastUpdated = await kv.get('last_updated');
  
  // If we have data that was updated in the last hour, return it
  if (cachedData && lastUpdated) {
    const lastUpdatedTime = new Date(lastUpdated);
    const currentTime = new Date();
    
    if ((currentTime - lastUpdatedTime) < 3600000) { // 1 hour in milliseconds
      return res.status(200).json({
        data: cachedData,
        lastUpdated: lastUpdated
      });
    }
  }
  
  // Otherwise, fetch new data
  const tvlData = {};
  const priceData = {};
  
  // Fetch data for each blockchain
  for (const [blockchain, ids] of Object.entries(BLOCKCHAIN_MAPPING)) {
    tvlData[blockchain] = await fetchTvlData(ids.defillama);
    
    // Add a small delay to avoid rate limiting
    await new Promise(resolve => setTimeout(resolve, 1000));
    
    priceData[blockchain] = await fetchPriceData(ids.coingecko);
    
    // Add another small delay
    await new Promise(resolve => setTimeout(resolve, 1000));
  }
  
  const newData = {
    tvl_data: tvlData,
    price_data: priceData
  };
  
  const newLastUpdated = new Date().toISOString();
  
  // Store the data in KV
  await kv.set('blockchain_data', newData);
  await kv.set('last_updated', newLastUpdated);
  
  // Return the data
  res.status(200).json({
    data: newData,
    lastUpdated: newLastUpdated
  });
} 