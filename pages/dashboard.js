import { useState, useEffect } from 'react';
import Head from 'next/head';
import { Box, Container, Typography, Grid, Paper, Button, CircularProgress } from '@mui/material';
import RefreshIcon from '@mui/icons-material/Refresh';
import BlockchainCard from '../components/BlockchainCard';
import styles from '../styles/Dashboard.module.css';

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

export default function Dashboard() {
  const [data, setData] = useState({});
  const [lastUpdated, setLastUpdated] = useState(null);
  const [loading, setLoading] = useState(true);
  const [refreshing, setRefreshing] = useState(false);

  const fetchData = async () => {
    try {
      const response = await fetch('/api/blockchain-data');
      const result = await response.json();
      
      setData(result.data);
      setLastUpdated(new Date(result.lastUpdated));
      setLoading(false);
      setRefreshing(false);
    } catch (error) {
      console.error('Error fetching data:', error);
      setLoading(false);
      setRefreshing(false);
    }
  };

  useEffect(() => {
    fetchData();
    
    // Set up interval to refresh data every hour
    const intervalId = setInterval(fetchData, 3600000);
    
    // Clean up interval on component unmount
    return () => clearInterval(intervalId);
  }, []);

  const handleRefresh = () => {
    setRefreshing(true);
    fetchData();
  };

  if (loading) {
    return (
      <Box className={styles.loadingContainer}>
        <CircularProgress />
        <Typography variant="h6" sx={{ mt: 2 }}>
          Loading dashboard data...
        </Typography>
      </Box>
    );
  }

  return (
    <>
      <Head>
        <title>Token Relations Dashboard</title>
        <meta name="description" content="Blockchain metrics dashboard" />
      </Head>
      
      <Container maxWidth="xl" className={styles.container}>
        <Box className={styles.header}>
          <Typography variant="h3" component="h1" gutterBottom>
            Token Relations Dashboard 📊
          </Typography>
          
          <Box className={styles.headerActions}>
            {lastUpdated && (
              <Typography variant="body2" className={styles.lastUpdated}>
                Last updated: {lastUpdated.toUTCString()}
              </Typography>
            )}
            
            <Button 
              variant="contained" 
              startIcon={<RefreshIcon />}
              onClick={handleRefresh}
              disabled={refreshing}
              className={styles.refreshButton}
            >
              {refreshing ? 'Refreshing...' : 'Refresh Data Now'}
            </Button>
          </Box>
        </Box>

        {Object.keys(BLOCKCHAIN_MAPPING).map((blockchain) => (
          <BlockchainCard 
            key={blockchain}
            name={blockchain}
            tvlData={data.tvl_data?.[blockchain] || []}
            priceData={data.price_data?.[blockchain] || []}
          />
        ))}
      </Container>
    </>
  );
} 