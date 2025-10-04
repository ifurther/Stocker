import { Client } from '@line/bot-sdk';
import { ChartJSNodeCanvas } from 'chartjs-node-canvas';
import AWS from 'aws-sdk';

// LINE SDK 設定
const client = new Client({
  channelAccessToken: ENV.LINE_CHANNEL_ACCESS_TOKEN,
  channelSecret: ENV.LINE_CHANNEL_SECRET
});

// R2 設定
const s3 = new AWS.S3({
  endpoint: 'https://<account_id>.r2.cloudflarestorage.com',
  accessKeyId: ENV.R2_KEY,
  secretAccessKey: ENV.R2_SECRET,
  signatureVersion: 'v4'
});

// ====== AI 股票代號解析 ====== 
async function resolveStockCode(userText, env) { 
  const prompt = ` 
  你是一個專門把輸入轉換成「台灣股市證券代號」的助手。 請只回傳數字代號，不要其他文字。 範例： 
  - 台灣積體電路製造股份有限公司 -> 2330 
  - 台積電 -> 2330 
  - TSMC -> 2330 
  - 聯發科 -> 2454 
  - MediaTek -> 2454 
  - 鴻海 -> 2317 
  - Hon Hai -> 2317 
  - Foxconn -> 2317 
  - 富邦金 -> 2881 
  - Fubon -> 2881 
  - 富邦金融控股股份有限公司 -> 2881 
  - 國泰金 -> 2882 
  - Cathay -> 2882 
  - 國泰金融控股股份有限公司 -> 2882 
  - 玉山金 -> 2884 - E.Sun -> 2884 
  - E.Sun FHC -> 2884 
  - 玉山金融控股股份有限公司 -> 2884 
  - 中信金 -> 2891 
  - CTBC -> 2891 
  - 中國信託金融控股股份有限公司 -> 2891 
  - 中華電信 -> 2412 
  - Chunghwa Telecom -> 2412 
  現在輸入：${userText} 
  輸出： 
  `; 
  const aiResponse = await env.AI.run("@cf/meta/llama-2-7b-chat-int8", { prompt, }); 
  return aiResponse.trim(); // 預期結果像 "2330" }

// JS 生成圖表
async function plotKD_SMA(stockCode, data) {
  const width = 800, height = 600;
  const chartJSNodeCanvas = new ChartJSNodeCanvas({ width, height });

  const configuration = {
    type: 'candlestick',
    data: {
      labels: data.map(d => d.date),
      datasets: [
        { label: 'K線', data: data.map(d => ({ o: d.open, h: d.high, l: d.low, c: d.close })) },
        { label: 'SMA20', type: 'line', data: data.map(d => d.SMA_20), borderColor: 'blue', fill: false },
        { label: 'KD_K', type: 'line', data: data.map(d => d.KD_K), borderColor: 'green', fill: false, yAxisID: 'kd' },
        { label: 'KD_D', type: 'line', data: data.map(d => d.KD_D), borderColor: 'red', fill: false, yAxisID: 'kd' }
      ]
    },
    options: {
      scales: { kd: { position: 'right' } }
    }
  };

  return chartJSNodeCanvas.renderToBuffer(configuration);
}

// 上傳到 R2
async function uploadToR2(buffer, stockCode) {
  const Key = `${stockCode}_kd_sma.png`;
  await s3.putObject({
    Bucket: ENV.R2_BUCKET,
    Key,
    Body: buffer,
    ContentType: 'image/png'
  }).promise();
  return `https://${ENV.R2_BUCKET}.${ENV.R2_ACCOUNT}.r2.cloudflarestorage.com/${Key}`;
}

// Worker 主程式
export default {
  async fetch(request, env) {
    const url = new URL(request.url);
    if (url.pathname === '/webhook' && request.method === 'POST') {
      const body = await request.json();
      const event = body.events[0];
      const userText = event.message.text.trim();

      const stockCode = await resolveStockCode(userText, env);
      if (!stockCode) {
        await client.replyMessage(event.replyToken, { type: 'text', text: '找不到股票代號' });
        return new Response('OK');
      }

      // 從 D1 取資料
      const { results } = await env.DB.prepare(
        `SELECT 日期 as date, 開盤價 as open, 最高價 as high, 最低價 as low, 收盤價 as close, KD_K, KD_D, SMA_20
         FROM stock_kd JOIN stock_sma USING(證券代號, 日期)
         WHERE 證券代號=? ORDER BY 日期 DESC LIMIT 50`
      ).bind(stockCode).all();

      if (results.length === 0) {
        await client.replyMessage(event.replyToken, { type: 'text', text: `找不到 ${stockCode} 的資料` });
        return new Response('OK');
      }

      // 生成圖表
      const buffer = await plotKD_SMA(stockCode, results);
      const imageUrl = await uploadToR2(buffer, stockCode);

      // 回覆 LINE 圖片訊息
      await client.replyMessage(event.replyToken, {
        type: 'image',
        originalContentUrl: imageUrl,
        previewImageUrl: imageUrl
      });

      return new Response('OK');
    }

    return new Response('Not found', { status: 404 });
  }
};
