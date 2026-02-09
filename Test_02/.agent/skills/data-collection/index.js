/**
 * 텔레그램 데이터 수집 메인 엔트리 포인트
 * Stock Research ONE /01-data-collection 워크플로우 실행
 */

require('dotenv').config();
const RealtimeDataProcessor = require('./realtime-processor');
const ChannelManager = require('./channel-manager');
const winston = require('winston');

// 로깅 설정
const logger = winston.createLogger({
    level: 'info',
    format: winston.format.combine(
        winston.format.timestamp(),
        winston.format.errors({ stack: true }),
        winston.format.json()
    ),
    defaultMeta: { service: 'telegram-data-collection' },
    transports: [
        new winston.transports.File({ filename: 'logs/error.log', level: 'error' }),
        new winston.transports.File({ filename: 'logs/combined.log' }),
        new winston.transports.Console({
            format: winston.format.simple()
        })
    ]
});

class TelegramDataCollectionService {
    constructor() {
        this.processor = null;
        this.isRunning = false;
        this.setupGracefulShutdown();
    }

    /**
     * 서비스 초기화
     */
    async initialize() {
        try {
            logger.info('Initializing Telegram Data Collection Service...');

            // 설정 로드
            const config = this.loadConfiguration();
            
            // 실시간 프로세서 생성
            this.processor = new RealtimeDataProcessor(config);
            
            // 이벤트 리스너 설정
            this.setupEventListeners();
            
            logger.info('Service initialized successfully');
            return true;

        } catch (error) {
            logger.error('Failed to initialize service:', error);
            throw error;
        }
    }

    /**
     * 설정 로드
     */
    loadConfiguration() {
        return {
            telegram: {
                token: process.env.TELEGRAM_BOT_TOKEN,
                channels: this.getChannelList(),
                keywords: this.getKeywordList(),
                stocks: this.getStockList()
            },
            filters: {
                minReliability: parseInt(process.env.MIN_RELIABILITY) || 50,
                enableSpamFilter: process.env.ENABLE_SPAM_FILTER === 'true',
                maxMessagesPerMinute: parseInt(process.env.MAX_MESSAGES_PER_MINUTE) || 100
            }
        };
    }

    /**
     * 모니터링할 채널 목록
     */
    getChannelList() {
        const defaultChannels = [
            '@korea_stock_realtime',
            '@miraeasset_news',
            '@kiwoom_news',
            '@maekyung_economy',
            '@hankyung_economy',
            '@stock_master_kr',
            '@semiconductor_kr'
        ];

        const customChannels = process.env.TELEGRAM_CHANNELS 
            ? process.env.TELEGRAM_CHANNELS.split(',')
            : [];

        return [...defaultChannels, ...customChannels].map(ch => ch.trim());
    }

    /**
     * 모니터링할 키워드 목록
     */
    getKeywordList() {
        const defaultKeywords = [
            '삼성전자', 'LG에너지솔루션', 'SK하이닉스', '삼성바이오로직스',
            '반도체', 'AI', '2차전지', '바이오', 'IT',
            '상승', '하락', '급등', '급락', '목표가', '실적', '공시'
        ];

        const customKeywords = process.env.MONITOR_KEYWORDS
            ? process.env.MONITOR_KEYWORDS.split(',')
            : [];

        return [...defaultKeywords, ...customKeywords].map(kw => kw.trim());
    }

    /**
     * 모니터링할 종목코드 목록
     */
    getStockList() {
        const defaultStocks = [
            '005930',  // 삼성전자
            '373220',  // LG에너지솔루션
            '000660',  // SK하이닉스
            '207940',  // 삼성바이오로직스
            '068270',  // 셀트리온
            '005490',  // POSCO홀딩스
            '035420',  // NAVER
            '035720',  // 카카오
            '005380',  // 현대차
            '000270',  // 기아
        ];

        const customStocks = process.env.MONITOR_STOCKS
            ? process.env.MONITOR_STOCKS.split(',')
            : [];

        return [...defaultStocks, ...customStocks].map(stock => stock.trim());
    }

    /**
     * 이벤트 리스너 설정
     */
    setupEventListeners() {
        if (!this.processor) return;

        // 메시지 처리 완료
        this.processor.on('messageProcessed', (message) => {
            logger.info('Message processed', {
                messageId: message.metadata.messageId,
                channel: message.metadata.channel,
                sentiment: message.sentiment.sentiment,
                stocks: message.entities.stocks.length
            });
        });

        // 긴급 메시지
        this.processor.on('urgentMessage', (message) => {
            logger.warn('Urgent message detected', {
                messageId: message.metadata.messageId,
                channel: message.metadata.channel,
                text: message.metadata.text.substring(0, 100),
                urgency: message.urgency.score
            });

            // 여기에 알림 시스템 연동 가능
        });

        // 긍정적 시그널
        this.processor.on('positiveSignal', (message) => {
            logger.info('Positive investment signal', {
                messageId: message.metadata.messageId,
                channel: message.metadata.channel,
                reliability: message.reliability.score,
                stocks: message.entities.stocks
            });
        });

        // 부정적 시그널
        this.processor.on('negativeSignal', (message) => {
            logger.warn('Negative investment signal', {
                messageId: message.metadata.messageId,
                channel: message.metadata.channel,
                reliability: message.reliability.score,
                stocks: message.entities.stocks
            });
        });

        // 종목 언급
        this.processor.on('stockMention', (message) => {
            logger.info('Stock mentioned', {
                messageId: message.metadata.messageId,
                channel: message.metadata.channel,
                stocks: message.entities.stocks,
                sentiment: message.sentiment.sentiment
            });
        });

        // 통계 정보
        this.processor.on('statistics', (stats) => {
            logger.info('Processing statistics', {
                totalProcessed: stats.totalProcessed,
                successRate: stats.successRate,
                channelsActive: stats.channelsActive,
                recentSentiment: stats.recentSentiment
            });

            // 1시간마다 상세 리포트 생성
            if (stats.runtime % (1000 * 60 * 60) < 60000) {
                this.generateHourlyReport();
            }
        });

        // 에러 처리
        this.processor.on('error', (error) => {
            logger.error('Processor error', { error: error.message, stack: error.stack });
        });

        this.processor.on('processingError', (error) => {
            logger.error('Message processing error', { error: error.message });
        });
    }

    /**
     * 서비스 시작
     */
    async start() {
        try {
            if (this.isRunning) {
                logger.warn('Service is already running');
                return;
            }

            logger.info('Starting Telegram Data Collection Service...');
            
            await this.processor.start();
            this.isRunning = true;
            
            logger.info('Service started successfully');
            console.log('🚀 Telegram Data Collection Service is running...');
            console.log('📊 Monitoring channels:', this.getChannelList().length);
            console.log('🔍 Monitoring keywords:', this.getKeywordList().length);
            console.log('📈 Monitoring stocks:', this.getStockList().length);

        } catch (error) {
            logger.error('Failed to start service:', error);
            throw error;
        }
    }

    /**
     * 서비스 중지
     */
    async stop() {
        try {
            if (!this.isRunning) {
                logger.warn('Service is not running');
                return;
            }

            logger.info('Stopping Telegram Data Collection Service...');
            
            await this.processor.stop();
            this.isRunning = false;
            
            logger.info('Service stopped successfully');
            console.log('🛑 Telegram Data Collection Service stopped');

        } catch (error) {
            logger.error('Failed to stop service:', error);
            throw error;
        }
    }

    /**
     * 시간별 리포트 생성
     */
    async generateHourlyReport() {
        try {
            if (!this.processor) return;

            const report = this.processor.generateInvestmentPsychologyReport();
            
            logger.info('Hourly investment psychology report generated', {
                totalMessages: report.summary.totalMessages,
                marketMood: report.summary.marketMood,
                topStocks: report.topStocks.slice(0, 5),
                generatedAt: report.generatedAt
            });

            // 파일로 저장 (선택적)
            const fs = require('fs');
            const path = require('path');
            
            const reportPath = path.join(__dirname, '../reports', `hourly-report-${Date.now()}.json`);
            fs.writeFileSync(reportPath, JSON.stringify(report, null, 2));
            
            logger.info(`Report saved to: ${reportPath}`);

        } catch (error) {
            logger.error('Failed to generate hourly report:', error);
        }
    }

    /**
     * 상태 확인
     */
    getStatus() {
        if (!this.processor) {
            return { status: 'Not initialized' };
        }

        return {
            isRunning: this.isRunning,
            ...this.processor.getStatus(),
            uptime: this.isRunning ? process.uptime() : 0,
            memoryUsage: process.memoryUsage()
        };
    }

    /**
     * 채널 관리자 접근
     */
    getChannelManager() {
        return this.processor?.getChannelManager();
    }

    /**
     * 처리된 메시지 조회
     */
    getProcessedMessages(limit = 100, filters = {}) {
        if (!this.processor) return [];
        return this.processor.getProcessedMessages(limit, filters);
    }

    /**
     * 그레이스풀 셧다운 설정
     */
    setupGracefulShutdown() {
        const shutdown = async (signal) => {
            console.log(`\nReceived ${signal}. Shutting down gracefully...`);
            
            if (this.isRunning) {
                await this.stop();
            }
            
            console.log('Graceful shutdown completed');
            process.exit(0);
        };

        process.on('SIGTERM', () => shutdown('SIGTERM'));
        process.on('SIGINT', () => shutdown('SIGINT'));
        process.on('SIGUSR2', () => shutdown('SIGUSR2')); // nodemon restart
    }
}

// CLI 인터페이스
async function main() {
    const service = new TelegramDataCollectionService();

    const command = process.argv[2];
    
    try {
        switch (command) {
            case 'start':
                await service.initialize();
                await service.start();
                break;
                
            case 'status':
                await service.initialize();
                console.log(JSON.stringify(service.getStatus(), null, 2));
                break;
                
            case 'report':
                await service.initialize();
                const report = service.processor.generateInvestmentPsychologyReport();
                console.log(JSON.stringify(report, null, 2));
                break;
                
            case 'channels':
                await service.initialize();
                const channelManager = service.getChannelManager();
                console.log(JSON.stringify(channelManager.getStatistics(), null, 2));
                break;
                
            case 'messages':
                await service.initialize();
                const messages = service.getProcessedMessages(10);
                console.log(JSON.stringify(messages, null, 2));
                break;
                
            default:
                console.log(`
Usage: node index.js <command>

Commands:
  start     - Start the data collection service
  status    - Show service status
  report    - Generate investment psychology report
  channels  - Show channel statistics
  messages  - Show recent processed messages (last 10)

Environment Variables:
  TELEGRAM_BOT_TOKEN     - Telegram bot token (required)
  TELEGRAM_CHANNELS      - Comma-separated channel list (optional)
  MONITOR_KEYWORDS       - Comma-separated keywords (optional)
  MONITOR_STOCKS         - Comma-separated stock codes (optional)
  MIN_RELIABILITY        - Minimum reliability score (default: 50)
  ENABLE_SPAM_FILTER     - Enable spam filter (default: false)
  MAX_MESSAGES_PER_MINUTE - Rate limit (default: 100)
                `);
                process.exit(1);
        }
    } catch (error) {
        console.error('Error:', error.message);
        process.exit(1);
    }
}

// 서비스로 실행될 때
if (require.main === module) {
    main().catch(console.error);
}

module.exports = TelegramDataCollectionService;