import { useState } from 'react';
import { Box, Typography, Grid, Paper, Divider } from '@mui/material';
import dynamic from 'next/dynamic';
import styles from '../styles/BlockchainCard.module.css';

// Dynamically import Plotly to avoid SSR issues
const Plot = dynamic(() => import('react-plotly.js'), { ssr: false });

export default function BlockchainCard({ name, tvlData, priceData }) {
  // Format TVL data for plotting
  const formattedTvlData = tvlData.map(item => ({
    date: new Date(item.date),
    tvl: item.tvl
  }));

  // Format price data for plotting
  const formattedPriceData = priceData.map(item => ({
    date: new Date(item.date),
    price: item.price
  }));

  // Calculate metrics
  const currentTvl = formattedTvlData.length > 0 ? formattedTvlData[formattedTvlData.length - 1].tvl : 0;
  const monthAgoTvlIndex = formattedTvlData.length > 30 ? formattedTvlData.length - 31 : 0;
  const monthAgoTvl = formattedTvlData.length > 0 ? formattedTvlData[monthAgoTvlIndex].tvl : 0;
  const tvlMonthlyChange = monthAgoTvl > 0 ? ((currentTvl - monthAgoTvl) / monthAgoTvl) * 100 : 0;

  const currentPrice = formattedPriceData.length > 0 ? formattedPriceData[formattedPriceData.length - 1].price : 0;
  const monthAgoPriceIndex = formattedPriceData.length > 30 ? formattedPriceData.length - 31 : 0;
  const monthAgoPrice = formattedPriceData.length > 0 ? formattedPriceData[monthAgoPriceIndex].price : 0;
  const priceMonthlyChange = monthAgoPrice > 0 ? ((currentPrice - monthAgoPrice) / monthAgoPrice) * 100 : 0;

  return (
    <Paper elevation={2} className={styles.card}>
      <Typography variant="h4" component="h2" className={styles.title}>
        {name}
      </Typography>
      
      <Grid container spacing={3}>
        {/* TVL Chart */}
        <Grid item xs={12} md={6}>
          <Typography variant="h5" align="center" gutterBottom>
            Total Value Locked (TVL)
          </Typography>
          
          {formattedTvlData.length > 0 ? (
            <>
              <Box className={styles.chartContainer}>
                <Plot
                  data={[
                    {
                      x: formattedTvlData.map(d => d.date),
                      y: formattedTvlData.map(d => d.tvl),
                      type: 'scatter',
                      mode: 'lines',
                      name: 'TVL',
                      line: { color: '#3498db', width: 2 },
                      fill: 'tozeroy',
                      fillcolor: 'rgba(52, 152, 219, 0.2)'
                    }
                  ]}
                  layout={{
                    height: 400,
                    margin: { l: 50, r: 20, t: 30, b: 50 },
                    paper_bgcolor: 'white',
                    plot_bgcolor: 'white',
                    xaxis: {
                      title: 'Date',
                      showgrid: true,
                      gridcolor: 'rgba(230, 230, 230, 0.8)',
                      tickfont: { color: '#000000' },
                      titlefont: { color: '#000000' }
                    },
                    yaxis: {
                      title: 'TVL (USD)',
                      showgrid: true,
                      gridcolor: 'rgba(230, 230, 230, 0.8)',
                      tickprefix: '$',
                      tickfont: { color: '#000000' },
                      titlefont: { color: '#000000' }
                    },
                    hovermode: 'x unified'
                  }}
                  config={{ responsive: true }}
                  className={styles.chart}
                />
              </Box>
              
              <Grid container spacing={2} className={styles.metricsContainer}>
                <Grid item xs={6}>
                  <Paper className={styles.metricCard}>
                    <Typography variant="subtitle1" color="textSecondary">
                      Current TVL
                    </Typography>
                    <Typography variant="h5">
                      ${currentTvl.toLocaleString(undefined, { minimumFractionDigits: 2, maximumFractionDigits: 2 })}
                    </Typography>
                  </Paper>
                </Grid>
                
                <Grid item xs={6}>
                  <Paper className={styles.metricCard}>
                    <Typography variant="subtitle1" color="textSecondary">
                      30-Day Change
                    </Typography>
                    <Typography 
                      variant="h5" 
                      style={{ color: tvlMonthlyChange >= 0 ? 'green' : 'red' }}
                    >
                      {tvlMonthlyChange >= 0 ? '+' : ''}{tvlMonthlyChange.toFixed(2)}%
                    </Typography>
                  </Paper>
                </Grid>
              </Grid>
            </>
          ) : (
            <Typography variant="body1" align="center" className={styles.noData}>
              No TVL data available for {name}
            </Typography>
          )}
        </Grid>
        
        {/* Price Chart */}
        <Grid item xs={12} md={6}>
          <Typography variant="h5" align="center" gutterBottom>
            Price (USD)
          </Typography>
          
          {formattedPriceData.length > 0 ? (
            <>
              <Box className={styles.chartContainer}>
                <Plot
                  data={[
                    {
                      x: formattedPriceData.map(d => d.date),
                      y: formattedPriceData.map(d => d.price),
                      type: 'scatter',
                      mode: 'lines',
                      name: 'Price',
                      line: { color: '#2ecc71', width: 2 },
                      fill: 'tozeroy',
                      fillcolor: 'rgba(46, 204, 113, 0.2)'
                    }
                  ]}
                  layout={{
                    height: 400,
                    margin: { l: 50, r: 20, t: 30, b: 50 },
                    paper_bgcolor: 'white',
                    plot_bgcolor: 'white',
                    xaxis: {
                      title: 'Date',
                      showgrid: true,
                      gridcolor: 'rgba(230, 230, 230, 0.8)',
                      tickfont: { color: '#000000' },
                      titlefont: { color: '#000000' }
                    },
                    yaxis: {
                      title: 'Price (USD)',
                      showgrid: true,
                      gridcolor: 'rgba(230, 230, 230, 0.8)',
                      tickprefix: '$',
                      tickfont: { color: '#000000' },
                      titlefont: { color: '#000000' }
                    },
                    hovermode: 'x unified'
                  }}
                  config={{ responsive: true }}
                  className={styles.chart}
                />
              </Box>
              
              <Grid container spacing={2} className={styles.metricsContainer}>
                <Grid item xs={6}>
                  <Paper className={styles.metricCard}>
                    <Typography variant="subtitle1" color="textSecondary">
                      Current Price
                    </Typography>
                    <Typography variant="h5">
                      ${currentPrice.toLocaleString(undefined, { minimumFractionDigits: 4, maximumFractionDigits: 4 })}
                    </Typography>
                  </Paper>
                </Grid>
                
                <Grid item xs={6}>
                  <Paper className={styles.metricCard}>
                    <Typography variant="subtitle1" color="textSecondary">
                      30-Day Change
                    </Typography>
                    <Typography 
                      variant="h5" 
                      style={{ color: priceMonthlyChange >= 0 ? 'green' : 'red' }}
                    >
                      {priceMonthlyChange >= 0 ? '+' : ''}{priceMonthlyChange.toFixed(2)}%
                    </Typography>
                  </Paper>
                </Grid>
              </Grid>
            </>
          ) : (
            <Typography variant="body1" align="center" className={styles.noData}>
              No price data available for {name}
            </Typography>
          )}
        </Grid>
      </Grid>
    </Paper>
  );
} 