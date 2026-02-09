/**
 * 실시간 데이터 처리 모듈
 * 텔레그램 메시지를 실시간으로 수집하고 처리하는 코디네이터
 */

const EventEmitter = require('events');
const TelegramCollector = require('./telegram-collector');
const MessagePreprocessor = require('./message-preprocessor');
const ChannelManager = require('./channel-manager');

class RealtimeDataProcessor extends EventEmitter {
    constructor(config) {
        super();
        this.config = config;
        this.isRunning = false;
        this.processedMessages = [];
        this.stats = {
            totalProcessed: 0,
            successfulProcessed: 0,
            errors: 0,
            startTime: null
        };
        
        // 컴포넌트 초기화
        this.channelManager = new ChannelManager();
        this.telegramCollector = new TelegramCollector(config.telegram);
        this.messagePreprocessor = new MessagePreprocessor();
        
        // 이벤트 리스너 설정
        this.setupEventListeners();
    }

    /**
     * 이벤트 리스너 설정
     */
    setupEventListeners() {
        // 텔레그램 메시지 수집 이벤트
        this.telegramCollector.on('messageCollected', (message) => {
            this.processMessage(message);
        });

        // 에러 처리
        this.telegramCollector.on('error', (error) => {
            console.error('Telegram collector error:', error);
            this.stats.errors++;
            this.emit('error', error);
        });
    }

    /**
     * 실시간 데이터 처리 시작
     */
    async start() {
        try {
            console.log('Starting realtime data processor...');
            
            // 텔레그램 봇 초기화
            const initialized = await this.telegramCollector.initialize();
            if (!initialized) {
                throw new Error('Failed to initialize Telegram collector');
            }

            // 채널 설정 적용
            this.applyChannelSettings();

            // 키워드 설정 적용
            this.applyKeywordSettings();

            // 데이터 수집 시작
            await this.telegramCollector.startCollection();

            this.isRunning = true;
            this.stats.startTime = new Date();

            // 주기적인 통계 보고
            this.startStatisticsReporting();

            console.log('Realtime data processor started successfully');
            this.emit('started');

        } catch (error) {
            console.error('Failed to start realtime data processor:', error);
            this.emit('error', error);
            throw error;
        }
    }

    /**
     * 채널 설정 적용
     */
    applyChannelSettings() {
        const channels = this.channelManager.getActiveChannels();
        channels.forEach(channel => {
            this.telegramCollector.addChannel(channel.id);
        });
        console.log(`Applied ${channels.length} channel settings`);
    }

    /**
     * 키워드 설정 적용
     */
    applyKeywordSettings() {
        const channels = this.channelManager.getActiveChannels();
        const allKeywords = new Set();

        channels.forEach(channel => {
            channel.keywords.forEach(keyword => {
                allKeywords.add(keyword);
            });
        });

        // 기본 투자 키워드 추가
        const defaultKeywords = [
            '주식', '투자', '증권', '코스피', '코스닥', '상승', '하락',
            '급등', '급락', '수익', '손실', '목표가', '실적', '공시'
        ];

        [...allKeywords, ...defaultKeywords].forEach(keyword => {
            this.telegramCollector.addKeyword(keyword);
        });

        console.log(`Applied ${allKeywords.size + defaultKeywords.length} keywords`);
    }

    /**
     * 메시지 처리
     */
    async processMessage(rawMessage) {
        try {
            this.stats.totalProcessed++;

            // 메시지 전처리
            const processedMessage = this.messagePreprocessor.preprocessText(rawMessage.text);
            
            // 메타데이터 추가
            processedMessage.metadata = {
                messageId: rawMessage.id,
                channel: rawMessage.channel,
                timestamp: rawMessage.timestamp,
                userId: rawMessage.userId,
                userName: rawMessage.userName,
                views: rawMessage.views,
                forwards: rawMessage.forwards
            };

            // 처리된 메시지 저장
            this.processedMessages.push(processedMessage);
            
            // 채널 메시지 카운트 업데이트
            this.channelManager.updateMessageCount(rawMessage.channel);
            this.channelManager.updateLastMessageId(rawMessage.channel, rawMessage.id);

            this.stats.successfulProcessed++;

            // 처리된 메시지 이벤트 발생
            this.emit('messageProcessed', processedMessage);

            // 특정 조건에서 알림 발생
            this.checkNotificationConditions(processedMessage);

            // 메모리 관리 (최근 10000개 메시지만 유지)
            if (this.processedMessages.length > 10000) {
                this.processedMessages = this.processedMessages.slice(-10000);
            }

        } catch (error) {
            console.error('Error processing message:', error);
            this.stats.errors++;
            this.emit('processingError', error);
        }
    }

    /**
     * 알림 조건 확인
     */
    checkNotificationConditions(processedMessage) {
        // 긴급성 높은 메시지
        if (processedMessage.urgency.urgency === 'high') {
            this.emit('urgentMessage', processedMessage);
        }

        // 신뢰도 높은 긍정적 메시지
        if (processedMessage.reliability.reliability === 'high' && 
            processedMessage.sentiment.sentiment === 'positive') {
            this.emit('positiveSignal', processedMessage);
        }

        // 신뢰도 높은 부정적 메시지
        if (processedMessage.reliability.reliability === 'high' && 
            processedMessage.sentiment.sentiment === 'negative') {
            this.emit('negativeSignal', processedMessage);
        }

        // 주요 종목 언급
        if (processedMessage.entities.stocks.length > 0) {
            this.emit('stockMention', processedMessage);
        }
    }

    /**
     * 주기적 통계 보고 시작
     */
    startStatisticsReporting() {
        setInterval(() => {
            const stats = this.getCurrentStatistics();
            this.emit('statistics', stats);
        }, 60000); // 1분마다 통계 보고
    }

    /**
     * 현재 통계 정보
     */
    getCurrentStatistics() {
        const runtime = this.stats.startTime ? 
            Date.now() - this.stats.startTime.getTime() : 0;

        const recentMessages = this.processedMessages.slice(-100); // 최근 100개
        const recentSentiment = this.calculateRecentSentiment(recentMessages);

        return {
            ...this.stats,
            runtime,
            processedMessagesCount: this.processedMessages.length,
            channelsActive: this.channelManager.getActiveChannels().length,
            recentSentiment,
            successRate: this.stats.totalProcessed > 0 ? 
                (this.stats.successfulProcessed / this.stats.totalProcessed * 100).toFixed(2) : 0
        };
    }

    /**
     * 최근 감성 계산
     */
    calculateRecentSentiment(messages) {
        if (messages.length === 0) return null;

        const sentimentCounts = { positive: 0, negative: 0, neutral: 0 };
        
        messages.forEach(msg => {
            sentimentCounts[msg.sentiment.sentiment]++;
        });

        const total = sentimentCounts.positive + sentimentCounts.negative + sentimentCounts.neutral;
        
        return {
            ...sentimentCounts,
            dominant: this.getDominantSentiment(sentimentCounts),
            confidence: Math.max(...Object.values(sentimentCounts)) / total
        };
    }

    /**
     * 주요 감성 가져오기
     */
    getDominantSentiment(counts) {
        const maxCount = Math.max(counts.positive, counts.negative, counts.neutral);
        if (maxCount === counts.positive) return 'positive';
        if (maxCount === counts.negative) return 'negative';
        return 'neutral';
    }

    /**
     * 투자 심리 리포트 생성
     */
    generateInvestmentPsychologyReport() {
        const report = this.messagePreprocessor.generateInvestmentPsychologyReport(this.processedMessages);
        
        // 추가 통계 정보
        const channelStats = this.getChannelStatistics();
        const timeStats = this.getTimeBasedStatistics();

        return {
            ...report,
            channelAnalysis: channelStats,
            temporalAnalysis: timeStats,
            generatedAt: new Date()
        };
    }

    /**
     * 채널별 통계
     */
    getChannelStatistics() {
        const channelStats = {};
        
        this.processedMessages.forEach(msg => {
            const channel = msg.metadata.channel;
            if (!channelStats[channel]) {
                channelStats[channel] = {
                    totalMessages: 0,
                    sentimentCounts: { positive: 0, negative: 0, neutral: 0 },
                    averageUrgency: 0,
                    averageReliability: 0,
                    topStocks: {}
                };
            }

            const stats = channelStats[channel];
            stats.totalMessages++;
            stats.sentimentCounts[msg.sentiment.sentiment]++;
            
            // 평균 계산을 위해 누적
            stats.averageUrgency += msg.urgency.score;
            stats.averageReliability += msg.reliability.score;

            // 종목 빈도
            msg.entities.stocks.forEach(stock => {
                stats.topStocks[stock] = (stats.topStocks[stock] || 0) + 1;
            });
        });

        // 평균값 계산
        Object.values(channelStats).forEach(stats => {
            if (stats.totalMessages > 0) {
                stats.averageUrgency /= stats.totalMessages;
                stats.averageReliability /= stats.totalMessages;
            }
        });

        return channelStats;
    }

    /**
     * 시간별 통계
     */
    getTimeBasedStatistics() {
        const hourlyStats = {};
        const dailyStats = {};

        this.processedMessages.forEach(msg => {
            const date = new Date(msg.metadata.timestamp);
            const hour = date.getHours();
            const day = date.toDateString();

            // 시간별 통계
            if (!hourlyStats[hour]) {
                hourlyStats[hour] = { positive: 0, negative: 0, neutral: 0 };
            }
            hourlyStats[hour][msg.sentiment.sentiment]++;

            // 일별 통계
            if (!dailyStats[day]) {
                dailyStats[day] = { positive: 0, negative: 0, neutral: 0 };
            }
            dailyStats[day][msg.sentiment.sentiment]++;
        });

        return {
            hourlyPatterns: hourlyStats,
            dailyPatterns: dailyStats,
            mostActiveHour: this.findMostActiveHour(hourlyStats),
            mostActiveDay: this.findMostActiveDay(dailyStats)
        };
    }

    /**
     * 가장 활동적인 시간 찾기
     */
    findMostActiveHour(hourlyStats) {
        let maxHour = null;
        let maxCount = 0;

        Object.entries(hourlyStats).forEach(([hour, counts]) => {
            const total = counts.positive + counts.negative + counts.neutral;
            if (total > maxCount) {
                maxCount = total;
                maxHour = parseInt(hour);
            }
        });

        return maxHour;
    }

    /**
     * 가장 활동적인 날 찾기
     */
    findMostActiveDay(dailyStats) {
        let maxDay = null;
        let maxCount = 0;

        Object.entries(dailyStats).forEach(([day, counts]) => {
            const total = counts.positive + counts.negative + counts.neutral;
            if (total > maxCount) {
                maxCount = total;
                maxDay = day;
            }
        });

        return maxDay;
    }

    /**
     * 실시간 처리 중지
     */
    async stop() {
        console.log('Stopping realtime data processor...');
        
        this.isRunning = false;
        await this.telegramCollector.stopCollection();
        
        console.log('Realtime data processor stopped');
        this.emit('stopped');
    }

    /**
     * 상태 확인
     */
    getStatus() {
        return {
            isRunning: this.isRunning,
            stats: this.getCurrentStatistics(),
            channelCount: this.channelManager.getActiveChannels().length,
            uptime: this.stats.startTime ? Date.now() - this.stats.startTime.getTime() : 0
        };
    }

    /**
     * 처리된 메시지 가져오기
     */
    getProcessedMessages(limit = 100, filters = {}) {
        let messages = [...this.processedMessages];

        // 필터 적용
        if (filters.sentiment) {
            messages = messages.filter(msg => msg.sentiment.sentiment === filters.sentiment);
        }
        
        if (filters.channel) {
            messages = messages.filter(msg => msg.metadata.channel === filters.channel);
        }
        
        if (filters.urgency) {
            messages = messages.filter(msg => msg.urgency.urgency === filters.urgency);
        }
        
        if (filters.minReliability) {
            messages = messages.filter(msg => msg.reliability.score >= filters.minReliability);
        }

        // 최신순 정렬 및 제한
        return messages.slice(-limit).reverse();
    }

    /**
     * 채널 매니저 접근
     */
    getChannelManager() {
        return this.channelManager;
    }

    /**
     * 텔레그램 컬렉터 접근
     */
    getTelegramCollector() {
        return this.telegramCollector;
    }
}

module.exports = RealtimeDataProcessor;