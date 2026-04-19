import 'dotenv/config';
import express from 'express';
import cors from 'cors';
import helmet from 'helmet';
import compression from 'compression';
import rateLimit from 'express-rate-limit';
import { initDatabase } from './database/connection';
import { initRedis } from './config/redis';
import { startCronJobs } from './jobs/dataSync';
import teamsRouter from './routes/teams';
import playersRouter from './routes/players';
import gamesRouter from './routes/games';
import predictionsRouter from './routes/predictions';
import analyticsRouter from './routes/analytics';
import authRouter from './routes/auth';
import { errorHandler } from './middleware/errorHandler';
import { logger } from './config/logger';

const app = express();
const PORT = process.env.PORT || 3001;

app.use(helmet());
app.use(cors({ origin: process.env.FRONTEND_URL || 'http://localhost:3000', credentials: true }));
app.use(compression());
app.use(express.json());
app.use(express.urlencoded({ extended: true }));

const limiter = rateLimit({ windowMs: 15 * 60 * 1000, max: 500 });
app.use('/api', limiter);

app.get('/health', (_req, res) => res.json({ status: 'ok', timestamp: new Date().toISOString() }));

app.use('/api/v1/teams', teamsRouter);
app.use('/api/v1/players', playersRouter);
app.use('/api/v1/games', gamesRouter);
app.use('/api/v1/predictions', predictionsRouter);
app.use('/api/v1/analytics', analyticsRouter);
app.use('/api/v1/auth', authRouter);

app.use(errorHandler);

async function start() {
  try {
    await initDatabase();
    await initRedis();
    startCronJobs();
    app.listen(PORT, () => logger.info(`Backend running on port ${PORT}`));
  } catch (err) {
    logger.error('Failed to start server', err);
    process.exit(1);
  }
}

start();

export default app;
