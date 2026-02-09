/**
 * 텔레그램 Bot API 연동 클래스
 * 특정 채널의 메시지를 수집하고 키워드 필터링을 수행
 */

const TelegramBot = require('node-telegram-bot-api');
const EventEmitter = require('events');

class TelegramCollector extends EventEmitter {
    constructor(config) {
        super();
        this.token = config.token;
        this.channels = config.channels || [];
        this.keywords = config.keywords || [];
        this.stocks = config.stocks || [];
        this.bot = null;
        this.isRunning = false;
        this.collectedMessages = [];
    }

    /**
     * 텔레그램 봇 초기화
     */
    async initialize() {
        try {
            this.bot = new TelegramBot(this.token, { polling: false });
            console.log('Telegram bot initialized successfully');
            return true;
        } catch (error) {
            console.error('Failed to initialize Telegram bot:', error);
            return false;
        }
    }

    /**
     * 채널 메시지 수집 시작
     */
    async startCollection() {
        if (!this.bot) {
            throw new Error('Bot not initialized. Call initialize() first.');
        }

        this.isRunning = true;
        console.log('Starting Telegram message collection...');

        // 각 채널에 대한 메시지 수집 설정
        for (const channel of this.channels) {
            this.setupChannelMonitoring(channel);
        }

        // 실시간 모니터링 설정
        this.setupRealtimeMonitoring();
    }

    /**
     * 특정 채널 모니터링 설정
     */
    setupChannelMonitoring(channel) {
        setInterval(async () => {
            if (!this.isRunning) return;

            try {
                const messages = await this.getChannelMessages(channel);
                this.processMessages(messages, channel);
            } catch (error) {
                console.error(`Error monitoring channel ${channel}:`, error);
            }
        }, 60000); // 1분마다 체크
    }

    /**
     * 실시간 모니터링 설정
     */
    setupRealtimeMonitoring() {
        // 텔레그램 업데이트 수신 설정
        this.bot.on('message', (msg) => {
            this.handleNewMessage(msg);
        });

        this.bot.on('channel_post', (msg) => {
            this.handleNewMessage(msg);
        });

        // 폴링 시작
        this.bot.startPolling();
    }

    /**
     * 채널 메시지 가져오기
     */
    async getChannelMessages(channelId, limit = 20) {
        try {
            // 실제 구현에서는 getChatHistory 같은 API 사용
            // 여기서는 샘플 데이터 반환
            return [];
        } catch (error) {
            console.error('Failed to get channel messages:', error);
            return [];
        }
    }

    /**
     * 새 메시지 처리
     */
    handleNewMessage(message) {
        if (!this.isRunning) return;

        const processedMessage = this.preprocessMessage(message);
        
        if (this.isRelevantMessage(processedMessage)) {
            this.collectedMessages.push(processedMessage);
            this.emit('messageCollected', processedMessage);
        }
    }

    /**
     * 메시지 전처리
     */
    preprocessMessage(message) {
        return {
            id: message.message_id,
            text: message.text || message.caption || '',
            timestamp: new Date(message.date * 1000),
            channel: message.chat.title || message.chat.username,
            channelType: message.chat.type,
            userId: message.from?.id,
            userName: message.from?.username,
            views: message.views || 0,
            forwards: message.forwards || 0,
            replyToMessageId: message.reply_to_message?.message_id,
            entities: message.entities || [],
            originalMessage: message
        };
    }

    /**
     * 관련 메시지 필터링
     */
    isRelevantMessage(message) {
        const text = message.text.toLowerCase();
        
        // 키워드 필터링
        const hasKeyword = this.keywords.some(keyword => 
            text.includes(keyword.toLowerCase())
        );
        
        // 종목코드 필터링
        const hasStock = this.stocks.some(stock => 
            text.includes(stock.toLowerCase())
        );

        return hasKeyword || hasStock || this.isInvestmentRelated(text);
    }

    /**
     * 투자 관련 텍스트인지 확인
     */
    isInvestmentRelated(text) {
        const investmentTerms = [
            '주식', '코스피', '코스닥', '투자', '증권', '주가', '상장',
            '수익률', '배당', '펀드', 'ETF', '선물', '옵션', '코인'
        ];
        
        return investmentTerms.some(term => text.includes(term));
    }

    /**
     * 메시지 일괄 처리
     */
    processMessages(messages, channel) {
        messages.forEach(message => {
            this.handleNewMessage(message);
        });
    }

    /**
     * 채널 추가
     */
    addChannel(channelId) {
        if (!this.channels.includes(channelId)) {
            this.channels.push(channelId);
            this.setupChannelMonitoring(channelId);
        }
    }

    /**
     * 키워드 추가
     */
    addKeyword(keyword) {
        if (!this.keywords.includes(keyword)) {
            this.keywords.push(keyword);
        }
    }

    /**
     * 종목 추가
     */
    addStock(stockCode) {
        if (!this.stocks.includes(stockCode)) {
            this.stocks.push(stockCode);
        }
    }

    /**
     * 수집된 메시지 가져오기
     */
    getCollectedMessages(limit = 100) {
        return this.collectedMessages.slice(-limit);
    }

    /**
     * 메시지 수집 중지
     */
    stopCollection() {
        this.isRunning = false;
        if (this.bot) {
            this.bot.stopPolling();
        }
        console.log('Telegram message collection stopped');
    }

    /**
     * 통계 정보 반환
     */
    getStatistics() {
        const now = new Date();
        const today = new Date(now.getFullYear(), now.getMonth(), now.getDate());
        
        const todayMessages = this.collectedMessages.filter(msg => 
            msg.timestamp >= today
        );

        const channelStats = {};
        this.collectedMessages.forEach(msg => {
            channelStats[msg.channel] = (channelStats[msg.channel] || 0) + 1;
        });

        return {
            totalMessages: this.collectedMessages.length,
            todayMessages: todayMessages.length,
            channelsCount: this.channels.length,
            keywordsCount: this.keywords.length,
            stocksCount: this.stocks.length,
            channelStats
        };
    }
}

module.exports = TelegramCollector;